"""
member.py — Rotating Sequencer Atomic Broadcast

Member tracks global ordering and calls deliver_callback(global_seq, rid, payload)
for each request in order. On the submitting node, it also sets the caller's
threading.Event so the gRPC thread can wake up and do its own DB write.

The deliver_callback is called AFTER event.set(), so a slow or failing callback
on the submitting replica never blocks the gRPC response.
"""

import logging
import socket
import threading
import time

from sequencer.messages import (
    BaseMessage,
    RequestMessage,
    SequenceMessage,
    RetransmitMessage,
    make_retransmit_req,
    make_retransmit_seq,
    RETRANSMIT_REQ,
    RETRANSMIT_SEQ,
)

logger = logging.getLogger(__name__)

_POLL = 0.005  # 5 ms polling interval
_RETRANSMIT_GAP = 0.5  # min seconds between retransmit requests


class Member:
    def __init__(self, member_id, n, peers, deliver_callback):
        self.id = member_id
        self.n = n
        self.peers = peers
        self._cb = (
            deliver_callback  # called for every delivered request on every replica
        )

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(peers[member_id])
        self._sock.settimeout(0.5)

        self._lock = threading.Lock()

        self._local_seq = 0  # monotonic counter for submit()
        self._next_deliver = 0  # next global seq we want to deliver
        self._next_assign = 0  # next global seq any node should assign

        self._requests: dict = {}  # rid -> RequestMessage
        self._assignments: dict = {}  # global_seq -> rid
        self._delivered: set = set()  # rids already delivered (popped from _requests)
        self._events: dict = {}  # rid -> threading.Event (submitting node only)
        self._rtx_times: dict = {}  # rate-limit retransmits

        self._running = False

    def start(self):
        self._running = True
        for fn in (self._recv_loop, self._sequencer_loop, self._deliver_loop):
            threading.Thread(target=fn, daemon=True).start()
        logger.info("Member %d started on %s", self.id, self.peers[self.id])

    def stop(self):
        self._running = False
        try:
            self._sock.close()
        except OSError:
            pass

    # ── Submit ─────────────────────────────────────────────────────────────────

    def submit(self, payload: bytes):
        """
        Broadcast payload. Returns (event, rid).
        Caller does event.wait() to block until global ordering slot is reached,
        then does its own DB write.
        """
        with self._lock:
            lsn = self._local_seq
            self._local_seq += 1
            rid = (self.id, lsn)
            event = threading.Event()
            self._events[rid] = event
            self._requests[rid] = RequestMessage(
                sender_id=self.id,
                local_seq_num=lsn,
                payload=payload,
                highest_global_recvd=max(self._assignments.keys(), default=-1),
                highest_delivered=self._next_deliver - 1,
                local_counts=[],
            )

        self._requests[rid].broadcast(self._sock, self.peers)
        logger.info("Member %d submitted rid=%s", self.id, rid)
        return event, rid

    # ── Receive loop ───────────────────────────────────────────────────────────

    def _recv_loop(self):
        while self._running:
            try:
                data, _ = self._sock.recvfrom(65535)
            except OSError:
                continue
            try:
                msg = BaseMessage.from_bytes(data)
            except Exception as e:
                logger.warning("Member %d bad datagram: %s", self.id, e)
                continue

            if isinstance(msg, RequestMessage):
                self._on_request(msg)
            elif isinstance(msg, SequenceMessage):
                self._on_sequence(msg)
            elif isinstance(msg, RetransmitMessage):
                self._on_retransmit(msg)

    def _on_request(self, msg: RequestMessage):
        rid = msg.request_id()
        with self._lock:
            if rid not in self._requests and rid not in self._delivered:
                self._requests[rid] = msg
        logger.debug("Member %d stored Request rid=%s", self.id, rid)

    def _on_sequence(self, msg: SequenceMessage):
        k = msg.global_seq_num
        rid = msg.request_id()
        with self._lock:
            if k not in self._assignments:
                self._assignments[k] = rid
                logger.info("Member %d stored Sequence k=%d rid=%s", self.id, k, rid)
            # All nodes advance _next_assign so they know who sequences k+1
            if k >= self._next_assign:
                self._next_assign = k + 1

    def _on_retransmit(self, msg: RetransmitMessage):
        if msg.retransmit_type == RETRANSMIT_REQ:
            rid = (msg.req_sender_id, msg.req_local_seq)
            with self._lock:
                req = self._requests.get(rid)
            if req is not None and req.sender_id == self.id:
                try:
                    req.send(self._sock, self.peers[msg.requester_id])
                except OSError:
                    pass

        elif msg.retransmit_type == RETRANSMIT_SEQ:
            k = msg.global_seq_num
            if k % self.n != self.id:
                return
            with self._lock:
                rid = self._assignments.get(k)
            if rid is not None:
                try:
                    self._make_seq_msg(k, rid).send(
                        self._sock, self.peers[msg.requester_id]
                    )
                except OSError:
                    pass

    # ── Sequencer loop ─────────────────────────────────────────────────────────

    def _sequencer_loop(self):
        while self._running:
            time.sleep(_POLL)
            chosen = self._try_sequence()
            if chosen is not None:
                k, rid = chosen
                try:
                    self._make_seq_msg(k, rid).broadcast(self._sock, self.peers)
                except OSError as e:
                    logger.warning("Member %d seq broadcast error: %s", self.id, e)

    def _try_sequence(self):
        """Under the lock: if it's our turn and preconditions met, assign k. Returns (k, rid) or None."""
        with self._lock:
            k = self._next_assign
            if k % self.n != self.id:
                return None

            # Precondition: have all prior SEQ assignments and their Request bodies
            for i in range(k):
                if i not in self._assignments:
                    self._rtx_seq(i)
                    return None
                prior_rid = self._assignments[i]
                if prior_rid not in self._requests and prior_rid not in self._delivered:
                    self._rtx_req(prior_rid)
                    return None

            # Pick any unassigned request whose prior local seqs are all assigned
            assigned = set(self._assignments.values())
            chosen = None
            for rid, req in self._requests.items():
                if rid in assigned:
                    continue
                if all(
                    (req.sender_id, i) in assigned for i in range(req.local_seq_num)
                ):
                    chosen = rid
                    break

            if chosen is None:
                return None

            self._assignments[k] = chosen
            self._next_assign = k + 1
            logger.info("Member %d assigned k=%d to rid=%s", self.id, k, chosen)
            return (k, chosen)

    # ── Deliver loop ───────────────────────────────────────────────────────────

    def _deliver_loop(self):
        while self._running:
            time.sleep(_POLL)
            self._try_deliver()

    def _try_deliver(self):
        """Check if the next global seq is deliverable; if so, deliver it."""
        with self._lock:
            s = self._next_deliver
            rid = self._assignments.get(s)
            if rid is None:
                return
            if rid not in self._requests:
                self._rtx_req(rid)
                return
            req = self._requests.pop(rid)
            event = self._events.pop(rid, None)
            self._delivered.add(rid)
            self._next_deliver = s + 1

        # --- outside the lock from here ---
        logger.info("Member %d delivering global_seq=%d rid=%s", self.id, s, rid)

        # Unblock the gRPC thread FIRST so it can return a response to the client.
        # The gRPC thread will do its own DB write after waking.
        if event is not None:
            event.set()

        # Then call the callback so non-submitting replicas also apply the write.
        # This runs on the deliver thread and must not block indefinitely.
        try:
            self._cb(s, rid, req.payload)
        except Exception:
            logger.exception("Member %d callback error global_seq=%d", self.id, s)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _make_seq_msg(self, k, rid) -> SequenceMessage:
        with self._lock:
            return SequenceMessage(
                global_seq_num=k,
                req_sender_id=rid[0],
                req_local_seq=rid[1],
                sequencer_id=self.id,
                highest_global_recvd=max(self._assignments.keys(), default=-1),
                highest_delivered=self._next_deliver - 1,
            )

    def _rtx_req(self, rid):
        """Rate-limited retransmit request for a missing RequestMessage. Call with lock held."""
        now = time.monotonic()
        key = ("req", rid)
        if now - self._rtx_times.get(key, 0) < _RETRANSMIT_GAP:
            return
        self._rtx_times[key] = now
        try:
            self._sock.sendto(
                make_retransmit_req(self.id, rid[0], rid[1]).to_bytes(),
                self.peers[rid[0]],
            )
        except OSError:
            pass

    def _rtx_seq(self, k):
        """Rate-limited retransmit request for a missing SequenceMessage. Call with lock held."""
        now = time.monotonic()
        key = ("seq", k)
        if now - self._rtx_times.get(key, 0) < _RETRANSMIT_GAP:
            return
        self._rtx_times[key] = now
        try:
            self._sock.sendto(
                make_retransmit_seq(self.id, k).to_bytes(), self.peers[k % self.n]
            )
        except OSError:
            pass
