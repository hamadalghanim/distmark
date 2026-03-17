"""
messages.py — Rotating Sequencer Atomic Broadcast Protocol
Wire format uses struct for compact, deterministic UDP serialisation.

Message type bytes:
    0x01  RequestMessage
    0x02  SequenceMessage
    0x03  RetransmitMessage

All integers are big-endian unsigned:
    B  = 1 byte  (uint8)
    H  = 2 bytes (uint16)
    I  = 4 bytes (uint32)

Retransmit sub-types:
    0x00  missing Request
    0x01  missing Sequence
"""

import socket
import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


MSG_REQUEST = 0x01
MSG_SEQUENCE = 0x02
MSG_RETRANSMIT = 0x03

RETRANSMIT_REQ = 0x00  # requesting a missing RequestMessage
RETRANSMIT_SEQ = 0x01  # requesting a missing SequenceMessage


class BaseMessage(ABC):
    """
    Abstract base for all protocol messages.

    Subclasses must implement:
        MSG_TYPE  (class-level int constant)
        _pack()   → bytes  (payload only, no type prefix)
        _unpack() (classmethod, receives payload bytes after type byte)

    The type byte is prepended by to_bytes() and stripped by from_bytes().
    """

    MSG_TYPE: int  # set by each subclass

    # ── Serialisation ────────────────────────────────────────────────────────

    @abstractmethod
    def _pack(self) -> bytes:
        """Encode this message to bytes (excluding the leading type byte)."""

    @classmethod
    @abstractmethod
    def _unpack(cls, data: bytes) -> "BaseMessage":
        """Decode from bytes (excluding the leading type byte)."""

    def to_bytes(self) -> bytes:
        """Full wire encoding: type byte + packed payload."""
        return struct.pack("!B", self.MSG_TYPE) + self._pack()

    @staticmethod
    def from_bytes(data: bytes) -> "BaseMessage":
        """
        Dispatch on the leading type byte and return the appropriate subclass.
        Raises ValueError on unknown type byte.
        """
        if len(data) < 1:
            raise ValueError("Empty datagram")
        msg_type = struct.unpack_from("!B", data, 0)[0]
        payload = data[1:]
        dispatch = {
            MSG_REQUEST: RequestMessage,
            MSG_SEQUENCE: SequenceMessage,
            MSG_RETRANSMIT: RetransmitMessage,
        }
        if msg_type not in dispatch:
            raise ValueError(f"Unknown message type: {msg_type:#04x}")
        return dispatch[msg_type]._unpack(payload)

    # ── Transport ────────────────────────────────────────────────────────────

    def send(self, sock: socket.socket, addr: tuple[str, int]) -> None:
        """Send this message to a single address."""
        sock.sendto(self.to_bytes(), addr)

    def broadcast(self, sock: socket.socket, peers: list[tuple[str, int]]) -> None:
        """Send this message to every peer address (including self if desired)."""
        encoded = self.to_bytes()
        for addr in peers:
            sock.sendto(encoded, addr)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        fields = ", ".join(
            f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_")
        )
        return f"{self.__class__.__name__}({fields})"


# ── RequestMessage ─────────────────────────────────────────────────────────────
#
# Sent by a group member when it receives an application request from a client.
# Broadcast to all members.
#
# Wire layout (after type byte):
#   B   sender_id
#   I   local_seq_num
#   I   highest_global_recvd   ← highest global seq num this sender has seen
#   I   highest_delivered      ← highest global seq num this sender has delivered
#   B   n_peers                ← length of local_counts array
#   n_peers × I  local_counts  ← local_counts[i] = highest local seq seen from member i
#   H   payload_len
#   payload_len × s  payload   ← raw application bytes


@dataclass
class RequestMessage(BaseMessage):
    """
    Broadcast when a member receives a client request.

    Attributes:
        sender_id            — member ID of the sender (0 … n-1)
        local_seq_num        — monotonically increasing counter on the sender;
                               together with sender_id forms the unique request ID
        payload              — raw application-level request bytes

        highest_global_recvd — piggybacked metadata: the highest global sequence
                               number this sender has seen in a SequenceMessage;
                               lets peers detect missing SequenceMessages
        highest_delivered    — piggybacked metadata: the highest global seq num
                               this sender has delivered to the application;
                               used to satisfy the majority delivery condition
        local_counts         — piggybacked metadata: local_counts[i] is the
                               highest local_seq_num seen from member i;
                               lets any node detect gaps in RequestMessages
                               from each sender and trigger retransmits
    """

    MSG_TYPE = MSG_REQUEST

    sender_id: int
    local_seq_num: int
    payload: bytes
    highest_global_recvd: int
    highest_delivered: int
    local_counts: list[int]  # length == n (number of members)

    def request_id(self) -> tuple[int, int]:
        """The unique request identifier <sender_id, local_seq_num>."""
        return (self.sender_id, self.local_seq_num)

    # ── Serialisation ────────────────────────────────────────────────────────

    def _pack(self) -> bytes:
        n = len(self.local_counts)
        header = struct.pack(
            "!Biib B",
            self.sender_id,
            self.local_seq_num,
            self.highest_global_recvd,
            self.highest_delivered,
            n,
        )
        counts = struct.pack(f"!{n}i", *self.local_counts)
        payload_len = struct.pack("!H", len(self.payload))
        return header + counts + payload_len + self.payload

    @classmethod
    def _unpack(cls, data: bytes) -> "RequestMessage":
        offset = 0

        sender_id, local_seq_num, highest_global_recvd, highest_delivered, n = (
            struct.unpack_from("!Biib B", data, offset)
        )
        offset += struct.calcsize("!Biib B")

        local_counts = list(struct.unpack_from(f"!{n}i", data, offset))
        offset += n * 4

        (payload_len,) = struct.unpack_from("!H", data, offset)
        offset += 2

        payload = data[offset : offset + payload_len]

        return cls(
            sender_id=sender_id,
            local_seq_num=local_seq_num,
            payload=payload,
            highest_global_recvd=highest_global_recvd,
            highest_delivered=highest_delivered,
            local_counts=local_counts,
        )


# ── SequenceMessage ────────────────────────────────────────────────────────────
#
# Sent by the current sequencer (member whose ID == k mod n) to assign global
# sequence number k to an unordered RequestMessage.
# Broadcast to all members.
#
# Wire layout (after type byte):
#   I   global_seq_num        ← k
#   B   req_sender_id         ← identifies which RequestMessage is being sequenced
#   I   req_local_seq         ←   "
#   B   sequencer_id          ← member ID of the sender (== k mod n; included for
#                               easy retransmit routing without arithmetic)
#   I   highest_global_recvd  ← piggybacked: highest global seq this sequencer has seen
#   I   highest_delivered     ← piggybacked: highest global seq this sequencer has delivered


@dataclass
class SequenceMessage(BaseMessage):
    """
    Assigns global sequence number k to a specific RequestMessage.

    Attributes:
        global_seq_num       — the global ordering index k being assigned
        req_sender_id        — sender_id field of the RequestMessage being sequenced
        req_local_seq        — local_seq_num field of the RequestMessage being sequenced
        sequencer_id         — member ID of the node sending this message (k mod n);
                               stored explicitly so retransmit recipients know where
                               to send a RetransmitMessage without recomputing k mod n
        highest_global_recvd — piggybacked: highest global seq this sequencer has seen;
                               peers use this to detect gaps in SequenceMessages
        highest_delivered    — piggybacked: highest global seq this sequencer has delivered;
                               contributes to the majority delivery condition check
    """

    MSG_TYPE = MSG_SEQUENCE

    global_seq_num: int
    req_sender_id: int
    req_local_seq: int
    sequencer_id: int
    highest_global_recvd: int
    highest_delivered: int

    def request_id(self) -> tuple[int, int]:
        """The request ID this sequence assignment refers to."""
        return (self.req_sender_id, self.req_local_seq)

    # ── Serialisation ────────────────────────────────────────────────────────

    # Format: I B I B i i
    _STRUCT = struct.Struct("!IBIBii")

    def _pack(self) -> bytes:
        return self._STRUCT.pack(
            self.global_seq_num,
            self.req_sender_id,
            self.req_local_seq,
            self.sequencer_id,
            self.highest_global_recvd,
            self.highest_delivered,
        )

    @classmethod
    def _unpack(cls, data: bytes) -> "SequenceMessage":
        (
            global_seq_num,
            req_sender_id,
            req_local_seq,
            sequencer_id,
            highest_global_recvd,
            highest_delivered,
        ) = cls._STRUCT.unpack_from(data)
        return cls(
            global_seq_num=global_seq_num,
            req_sender_id=req_sender_id,
            req_local_seq=req_local_seq,
            sequencer_id=sequencer_id,
            highest_global_recvd=highest_global_recvd,
            highest_delivered=highest_delivered,
        )


# ── RetransmitMessage ──────────────────────────────────────────────────────────
#
# Sent by a member when it detects a gap — either a missing RequestMessage or a
# missing SequenceMessage.  Sent directly (unicast) to the original sender of
# the missing message.
#
# Wire layout (after type byte):
#   B   requester_id     ← member sending this retransmit request
#   B   retransmit_type  ← RETRANSMIT_REQ (0x00) or RETRANSMIT_SEQ (0x01)
#
#   if RETRANSMIT_REQ:
#       B   req_sender_id   ← sender_id of the missing RequestMessage
#       I   req_local_seq   ← local_seq_num of the missing RequestMessage
#
#   if RETRANSMIT_SEQ:
#       I   global_seq_num  ← global seq num of the missing SequenceMessage


@dataclass
class RetransmitMessage(BaseMessage):
    """
    Negative-acknowledgement: asks the original sender to retransmit a message.

    Set retransmit_type to RETRANSMIT_REQ or RETRANSMIT_SEQ, then fill in
    the corresponding fields:

        RETRANSMIT_REQ  → set req_sender_id and req_local_seq
                          Send to: the member whose ID == req_sender_id
                          Trigger: a SequenceMessage refers to a (sender_id, local_seq)
                                   that is not yet in pending_requests; or local_counts
                                   from a peer reveals a gap in requests from a sender

        RETRANSMIT_SEQ  → set global_seq_num
                          Send to: the member whose ID == global_seq_num mod n
                                   (that member is the sequencer for that slot)
                          Trigger: a gap in seq_assignments keys; or a peer's
                                   highest_global_recvd exceeds our own max known seq
    """

    MSG_TYPE = MSG_RETRANSMIT

    requester_id: int
    retransmit_type: int  # RETRANSMIT_REQ or RETRANSMIT_SEQ

    # RETRANSMIT_REQ fields
    req_sender_id: Optional[int] = None
    req_local_seq: Optional[int] = None

    # RETRANSMIT_SEQ fields
    global_seq_num: Optional[int] = None

    def __post_init__(self):
        if self.retransmit_type == RETRANSMIT_REQ:
            if self.req_sender_id is None or self.req_local_seq is None:
                raise ValueError(
                    "RetransmitMessage(RETRANSMIT_REQ) requires req_sender_id and req_local_seq"
                )
        elif self.retransmit_type == RETRANSMIT_SEQ:
            if self.global_seq_num is None:
                raise ValueError(
                    "RetransmitMessage(RETRANSMIT_SEQ) requires global_seq_num"
                )
        else:
            raise ValueError(f"Unknown retransmit_type: {self.retransmit_type}")

    # ── Serialisation ────────────────────────────────────────────────────────

    _HEADER = struct.Struct("!BB")  # requester_id, retransmit_type
    _REQ_BODY = struct.Struct("!BI")  # req_sender_id, req_local_seq
    _SEQ_BODY = struct.Struct("!I")  # global_seq_num

    def _pack(self) -> bytes:
        header = self._HEADER.pack(self.requester_id, self.retransmit_type)
        if self.retransmit_type == RETRANSMIT_REQ:
            return header + self._REQ_BODY.pack(self.req_sender_id, self.req_local_seq)
        else:
            return header + self._SEQ_BODY.pack(self.global_seq_num)

    @classmethod
    def _unpack(cls, data: bytes) -> "RetransmitMessage":
        offset = 0
        requester_id, retransmit_type = cls._HEADER.unpack_from(data, offset)
        offset += cls._HEADER.size

        if retransmit_type == RETRANSMIT_REQ:
            req_sender_id, req_local_seq = cls._REQ_BODY.unpack_from(data, offset)
            return cls(
                requester_id=requester_id,
                retransmit_type=retransmit_type,
                req_sender_id=req_sender_id,
                req_local_seq=req_local_seq,
            )
        else:
            (global_seq_num,) = cls._SEQ_BODY.unpack_from(data, offset)
            return cls(
                requester_id=requester_id,
                retransmit_type=retransmit_type,
                global_seq_num=global_seq_num,
            )


# ── Convenience constructors ───────────────────────────────────────────────────


def make_retransmit_req(
    requester_id: int,
    req_sender_id: int,
    req_local_seq: int,
) -> RetransmitMessage:
    """Build a retransmit request for a missing RequestMessage."""
    return RetransmitMessage(
        requester_id=requester_id,
        retransmit_type=RETRANSMIT_REQ,
        req_sender_id=req_sender_id,
        req_local_seq=req_local_seq,
    )


def make_retransmit_seq(
    requester_id: int,
    global_seq_num: int,
) -> RetransmitMessage:
    """Build a retransmit request for a missing SequenceMessage."""
    return RetransmitMessage(
        requester_id=requester_id,
        retransmit_type=RETRANSMIT_SEQ,
        global_seq_num=global_seq_num,
    )


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    def _check(original: BaseMessage, label: str):
        wire = original.to_bytes()
        decoded = BaseMessage.from_bytes(wire)
        assert decoded.__dict__ == original.__dict__, (
            f"FAIL {label}:\n  original={original}\n  decoded ={decoded}"
        )
        print(f"  OK  {label:30s}  {len(wire)} bytes on wire")

    print("Running round-trip tests …\n")

    _check(
        RequestMessage(
            sender_id=2,
            local_seq_num=7,
            payload=b"hello world",
            highest_global_recvd=4,
            highest_delivered=3,
            local_counts=[3, 5, 7, 2],
        ),
        "RequestMessage",
    )

    _check(
        SequenceMessage(
            global_seq_num=5,
            req_sender_id=2,
            req_local_seq=7,
            sequencer_id=1,
            highest_global_recvd=4,
            highest_delivered=3,
        ),
        "SequenceMessage",
    )

    _check(
        RetransmitMessage(
            requester_id=0,
            retransmit_type=RETRANSMIT_REQ,
            req_sender_id=2,
            req_local_seq=7,
        ),
        "RetransmitMessage(REQ)",
    )

    _check(
        RetransmitMessage(
            requester_id=0,
            retransmit_type=RETRANSMIT_SEQ,
            global_seq_num=5,
        ),
        "RetransmitMessage(SEQ)",
    )

    _check(
        RequestMessage(
            sender_id=0,
            local_seq_num=0,
            payload=b"",
            highest_global_recvd=0,
            highest_delivered=0,
            local_counts=[0],
        ),
        "RequestMessage (empty payload, n=1)",
    )

    print("\nAll tests passed.")
    sys.exit(0)
