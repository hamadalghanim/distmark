"""
messages.py — Rotating Sequencer Atomic Broadcast Protocol
Wire format uses struct for compact, deterministic UDP serialisation.

Message type bytes:
    0x01  RequestMessage
    0x02  SequenceMessage
    0x03  RetransmitRequestMessage   (missing RequestMessage)
    0x04  RetransmitSequenceMessage  (missing SequenceMessage)

All integers are big-endian unsigned (! prefix, I/H/B = 4/2/1 bytes).
"""

import socket
import struct
from dataclasses import dataclass
from typing import ClassVar


# ── Registry ───────────────────────────────────────────────────────────────────

_REGISTRY: dict[int, type["BaseMessage"]] = {}


class BaseMessage:
    MSG_TYPE: ClassVar[int]
    _STRUCT: ClassVar[struct.Struct]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "MSG_TYPE"):
            _REGISTRY[cls.MSG_TYPE] = cls

    # ── Serialisation ────────────────────────────────────────────────────────

    def _fields(self) -> tuple:
        """Return field values in _STRUCT order. Override when non-trivial."""
        raise NotImplementedError

    def _pack(self) -> bytes:
        return self._STRUCT.pack(*self._fields())

    def to_bytes(self) -> bytes:
        return struct.pack("!B", self.MSG_TYPE) + self._pack()

    @classmethod
    def _unpack(cls, data: bytes) -> "BaseMessage":
        return cls(*cls._STRUCT.unpack_from(data))

    @staticmethod
    def from_bytes(data: bytes) -> "BaseMessage":
        if not data:
            raise ValueError("Empty datagram")
        msg_type = data[0]
        cls = _REGISTRY.get(msg_type)
        if cls is None:
            raise ValueError(f"Unknown message type: {msg_type:#04x}")
        return cls._unpack(data[1:])

    # ── Transport ────────────────────────────────────────────────────────────

    def send(self, sock: socket.socket, addr: tuple[str, int]) -> None:
        sock.sendto(self.to_bytes(), addr)

    def broadcast(self, sock: socket.socket, peers: list[tuple[str, int]]) -> None:
        encoded = self.to_bytes()
        for addr in peers:
            sock.sendto(encoded, addr)


# ── RequestMessage ─────────────────────────────────────────────────────────────
#
# Broadcast by a member when it receives a client request.
#
# Wire layout (after type byte):
#   B   sender_id
#   I   local_seq_num
#   I   highest_global_recvd
#   I   highest_delivered
#   B   n_peers
#   n × I  local_counts
#   H   payload_len
#   …   payload


@dataclass
class RequestMessage(BaseMessage):
    MSG_TYPE: ClassVar[int] = 0x01

    sender_id: int
    local_seq_num: int
    highest_global_recvd: int
    highest_delivered: int
    local_counts: list[int]
    payload: bytes

    def request_id(self) -> tuple[int, int]:
        return (self.sender_id, self.local_seq_num)

    def _pack(self) -> bytes:
        n = len(self.local_counts)
        return (
            struct.pack(
                "!BIiiB",
                self.sender_id,
                self.local_seq_num,
                self.highest_global_recvd,
                self.highest_delivered,
                n,
            )  # fmt: skip
            + struct.pack(f"!{n}I", *self.local_counts)
            + struct.pack("!H", len(self.payload))
            + self.payload
        )

    @classmethod
    def _unpack(cls, data: bytes) -> "RequestMessage":
        offset = 0
        sender_id, local_seq_num, highest_global_recvd, highest_delivered, n = (
            struct.unpack_from("!BIiiB", data, offset)
        )
        offset += struct.calcsize("!BIiiB")

        local_counts = list(struct.unpack_from(f"!{n}I", data, offset))
        offset += n * 4

        (payload_len,) = struct.unpack_from("!H", data, offset)
        offset += 2

        return cls(
            sender_id=sender_id,
            local_seq_num=local_seq_num,
            highest_global_recvd=highest_global_recvd,
            highest_delivered=highest_delivered,
            local_counts=local_counts,
            payload=data[offset : offset + payload_len],
        )


# ── SequenceMessage ────────────────────────────────────────────────────────────
#
# Broadcast by the current sequencer (member ID == k mod n) to assign global
# sequence number k to a RequestMessage.
#
# Wire layout (after type byte):
#   I   global_seq_num
#   B   req_sender_id
#   I   req_local_seq
#   B   sequencer_id
#   I   highest_global_recvd
#   I   highest_delivered


@dataclass
class SequenceMessage(BaseMessage):
    MSG_TYPE: ClassVar[int] = 0x02
    _STRUCT: ClassVar[struct.Struct] = struct.Struct("!IBIBii")

    global_seq_num: int
    req_sender_id: int
    req_local_seq: int
    sequencer_id: int
    highest_global_recvd: int
    highest_delivered: int

    def request_id(self) -> tuple[int, int]:
        return (self.req_sender_id, self.req_local_seq)

    def _fields(self):
        return (
            self.global_seq_num,
            self.req_sender_id,
            self.req_local_seq,
            self.sequencer_id,
            self.highest_global_recvd,
            self.highest_delivered,
        )


# ── RetransmitRequestMessage ───────────────────────────────────────────────────
#
# Unicast to req_sender_id when a gap in RequestMessages is detected.
#
# Wire layout (after type byte):
#   B   requester_id
#   B   req_sender_id
#   I   req_local_seq


@dataclass
class RetransmitRequestMessage(BaseMessage):
    MSG_TYPE: ClassVar[int] = 0x03
    _STRUCT: ClassVar[struct.Struct] = struct.Struct("!BBI")

    requester_id: int
    req_sender_id: int
    req_local_seq: int

    def _fields(self):
        return (self.requester_id, self.req_sender_id, self.req_local_seq)


# ── RetransmitSequenceMessage ──────────────────────────────────────────────────
#
# Unicast to (global_seq_num mod n) when a gap in SequenceMessages is detected.
#
# Wire layout (after type byte):
#   B   requester_id
#   I   global_seq_num


@dataclass
class RetransmitSequenceMessage(BaseMessage):
    MSG_TYPE: ClassVar[int] = 0x04
    _STRUCT: ClassVar[struct.Struct] = struct.Struct("!BI")

    requester_id: int
    global_seq_num: int

    def _fields(self):
        return (self.requester_id, self.global_seq_num)
