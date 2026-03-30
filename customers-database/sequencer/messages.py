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


# request message sent by a member when it receives a client request, before global sequence number assignment
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

MSG_REQUEST = 0x01  # to send the payload to all members
MSG_SEQUENCE = 0x02  # set the seq for the payload
MSG_RETRANSMIT_REQ = 0x03  # to request a retransmit of a missing RequestMessage
MSG_RETRANSMIT_SEQ = 0x04  # to request a retransmit of a missing SequenceMessage


@dataclass
class RequestMessage:
    sender_id: int
    local_seq_num: int
    highest_global_recvd: int
    highest_delivered: int
    local_counts: list[int]
    payload: bytes

    def request_id(self) -> tuple[int, int]:
        return (self.sender_id, self.local_seq_num)

    def to_bytes(self) -> bytes:
        n = len(self.local_counts)
        return (
            struct.pack("!B", MSG_REQUEST)
            + struct.pack(
                "!BIiiB",
                self.sender_id,
                self.local_seq_num,
                self.highest_global_recvd,
                self.highest_delivered,
                n,
            )
            + struct.pack(f"!{n}I", *self.local_counts)
            + struct.pack("!H", len(self.payload))
            + self.payload
        )

    @staticmethod
    def from_bytes(data: bytes) -> "RequestMessage":
        offset = 0
        sender_id, local_seq_num, highest_global_recvd, highest_delivered, n = (
            struct.unpack_from("!BIiiB", data, offset)
        )
        offset += struct.calcsize("!BIiiB")

        local_counts = list(struct.unpack_from(f"!{n}I", data, offset))
        offset += n * 4

        (payload_len,) = struct.unpack_from("!H", data, offset)
        offset += 2

        return RequestMessage(
            sender_id=sender_id,
            local_seq_num=local_seq_num,
            highest_global_recvd=highest_global_recvd,
            highest_delivered=highest_delivered,
            local_counts=local_counts,
            payload=data[offset : offset + payload_len],
        )


# sequence message for assigning global sequence numbers, sent by the current sequencer
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

_SEQ_STRUCT = struct.Struct("!IBIBii")


@dataclass
class SequenceMessage:
    global_seq_num: int
    req_sender_id: int
    req_local_seq: int
    sequencer_id: int
    highest_global_recvd: int
    highest_delivered: int

    def request_id(self) -> tuple[int, int]:
        return (self.req_sender_id, self.req_local_seq)

    def to_bytes(self) -> bytes:
        return struct.pack("!B", MSG_SEQUENCE) + _SEQ_STRUCT.pack(
            self.global_seq_num,
            self.req_sender_id,
            self.req_local_seq,
            self.sequencer_id,
            self.highest_global_recvd,
            self.highest_delivered,
        )

    @staticmethod
    def from_bytes(data: bytes) -> "SequenceMessage":
        return SequenceMessage(*_SEQ_STRUCT.unpack_from(data))


# retransmit message for missing RequestMessage
# Unicast to req_sender_id when a gap in RequestMessages is detected.
#
# Wire layout (after type byte):
#   B   requester_id
#   B   req_sender_id
#   I   req_local_seq

_RETRANSMIT_REQ_STRUCT = struct.Struct("!BBI")


@dataclass
class RetransmitRequestMessage:
    requester_id: int
    req_sender_id: int
    req_local_seq: int

    def to_bytes(self) -> bytes:
        return struct.pack("!B", MSG_RETRANSMIT_REQ) + _RETRANSMIT_REQ_STRUCT.pack(
            self.requester_id,
            self.req_sender_id,
            self.req_local_seq,
        )

    @staticmethod
    def from_bytes(data: bytes) -> "RetransmitRequestMessage":
        return RetransmitRequestMessage(*_RETRANSMIT_REQ_STRUCT.unpack_from(data))


# retransmit message for missing SequenceMessage
# Unicast to (global_seq_num mod n) when a gap in SequenceMessages is detected.
#
# Wire layout (after type byte):
#   B   requester_id
#   I   global_seq_num

_RETRANSMIT_SEQ_STRUCT = struct.Struct("!BI")


@dataclass
class RetransmitSequenceMessage:
    requester_id: int
    global_seq_num: int

    def to_bytes(self) -> bytes:
        return struct.pack("!B", MSG_RETRANSMIT_SEQ) + _RETRANSMIT_SEQ_STRUCT.pack(
            self.requester_id,
            self.global_seq_num,
        )

    @staticmethod
    def from_bytes(data: bytes) -> "RetransmitSequenceMessage":
        return RetransmitSequenceMessage(*_RETRANSMIT_SEQ_STRUCT.unpack_from(data))


# helper functions used by member

Message = (
    RequestMessage
    | SequenceMessage
    | RetransmitRequestMessage
    | RetransmitSequenceMessage
)

_DECODERS = {
    MSG_REQUEST: RequestMessage.from_bytes,
    MSG_SEQUENCE: SequenceMessage.from_bytes,
    MSG_RETRANSMIT_REQ: RetransmitRequestMessage.from_bytes,
    MSG_RETRANSMIT_SEQ: RetransmitSequenceMessage.from_bytes,
}


def decode(data: bytes) -> Message:
    if not data:
        raise ValueError("Empty datagram")
    msg_type = data[0]
    decoder = _DECODERS.get(msg_type)
    if decoder is None:
        raise ValueError(f"Unknown message type: {msg_type:#04x}")
    return decoder(data[1:])


def send(sock: socket.socket, msg: Message, addr: tuple[str, int]) -> None:
    sock.sendto(msg.to_bytes(), addr)


def broadcast(sock: socket.socket, msg: Message, peers: list[tuple[str, int]]) -> None:
    encoded = msg.to_bytes()
    for addr in peers:
        sock.sendto(encoded, addr)
