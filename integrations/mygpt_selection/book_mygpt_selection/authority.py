"""Memory-only Book authority for explicit, short-lived, revocable selection leases.

The same-process resolver capability is the trust root, not a self-asserted JSON
producer flag. This development contract is not Android IPC or multi-user TLS.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import hmac
import secrets
import threading
import time
from typing import Callable, Protocol, TypeVar
from .contract import BridgeError, HEX, Selection, canonical, digest, identifier, require

T = TypeVar('T')

class Source(Protocol):
    def project(self, selection: Selection) -> dict: ...

class Clock:
    def wall_ms(self) -> int:
        return time.time_ns() // 1_000_000
    def monotonic(self) -> float:
        return time.monotonic()

@dataclass
class Session:
    public_id: str
    issued_ms: int
    expires_ms: int
    deadline: float
    seq: int = 0
    epoch: int = 0
    revoked: bool = False
    active: dict | None = None
    lease_deadline: float = 0
    commands: dict = field(default_factory=dict)

class Authority:
    def __init__(self, source: Source, *, clock: Clock | None = None,
                 session_seconds: int = 900, lease_seconds: int = 90,
                 max_sessions: int = 16, command_capacity: int = 64):
        require(type(session_seconds) is int and 60 <= session_seconds <= 3600, 'INVALID_SESSION_TTL')
        require(type(lease_seconds) is int and 1 <= lease_seconds <= 300, 'INVALID_LEASE_TTL')
        require(type(max_sessions) is int and 1 <= max_sessions <= 64, 'INVALID_CAPACITY')
        require(type(command_capacity) is int and 1 <= command_capacity <= 256, 'INVALID_CAPACITY')
        self.source, self.clock = source, clock or Clock()
        self.session_seconds, self.lease_seconds = session_seconds, lease_seconds
        self.max_sessions, self.command_capacity = max_sessions, command_capacity
        self.issuer_id = 'book-' + secrets.token_hex(12)
        self._key = secrets.token_bytes(32)
        self._sessions: dict[str, Session] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _token_key(token: str) -> str:
        require(type(token) is str and len(token) == 64 and HEX.fullmatch(token) is not None,
                'UNAUTHORIZED', 403)
        return hashlib.sha256(token.encode('ascii')).hexdigest()

    def _live(self, session: Session) -> bool:
        return (not session.revoked and session.issued_ms <= self.clock.wall_ms() < session.expires_ms
                and self.clock.monotonic() < session.deadline)

    def _session(self, token: str) -> Session:
        session = self._sessions.get(self._token_key(token))
        require(session is not None and self._live(session), 'UNAUTHORIZED', 403)
        return session

    def authorize(self) -> tuple[str, dict]:
        with self._lock:
            self._sessions = {k: s for k, s in self._sessions.items() if self._live(s)}
            require(len(self._sessions) < self.max_sessions, 'SESSION_CAPACITY', 429)
            token = secrets.token_hex(32)
            now = self.clock.wall_ms()
            session = Session('session-' + secrets.token_hex(12), now, now + self.session_seconds * 1000,
                              self.clock.monotonic() + self.session_seconds)
            self._sessions[self._token_key(token)] = session
            return token, self._status(session)

    def _status(self, s: Session) -> dict:
        active = (s.active is not None and self.clock.monotonic() < s.lease_deadline
                  and s.active['issued_at_ms'] <= self.clock.wall_ms() < s.active['expires_at_ms'])
        return {'schema': 'book.selection-session.v1', 'session_id': s.public_id,
                'issuer_id': self.issuer_id, 'epoch': s.epoch, 'last_sequence': s.seq,
                'expires_at_ms': s.expires_ms, 'has_active_selection': active,
                'notes_exported': False, 'answers_exported': False}

    def status(self, token: str) -> dict:
        with self._lock:
            return self._status(self._session(token))

    @staticmethod
    def _command(seq: int, request_id: str) -> None:
        require(type(seq) is int and 1 <= seq <= 2**53 - 1, 'INVALID_SEQUENCE')
        identifier(request_id)

    def _begin(self, s: Session, seq: int, request_id: str, fingerprint: str) -> dict | None:
        previous = s.commands.get(request_id)
        if previous:
            require(previous['fingerprint'] == fingerprint, 'REQUEST_ID_CONFLICT', 409)
            require(previous['state'] != 'pending', 'REQUEST_PENDING', 409)
            if previous['state'] == 'failed':
                raise BridgeError(previous['code'], previous['status'])
            return deepcopy(previous['result'])
        require(seq > s.seq, 'OUT_OF_ORDER', 409)
        require(len(s.commands) < self.command_capacity, 'COMMAND_CAPACITY_RECONNECT', 429)
        # Reserve the sequence and invalidate first; slow older requests cannot win.
        s.seq, s.epoch, s.active = seq, s.epoch + 1, None
        s.commands[request_id] = {'fingerprint': fingerprint, 'state': 'pending'}
        return None

    def grant(self, token: str, selection: dict, expected_sha256: str,
              sequence: int, request_id: str) -> dict:
        self._command(sequence, request_id)
        selected = Selection.parse(selection)
        require(type(expected_sha256) is str and HEX.fullmatch(expected_sha256) is not None, 'INVALID_DIGEST')
        fp = digest({'op': 'select', 'selection': selected.json(), 'expected_sha256': expected_sha256,
                     'sequence': sequence})
        with self._lock:
            session = self._session(token)
            cached = self._begin(session, sequence, request_id, fp)
            epoch = session.epoch
        if cached is not None:
            self.resolve(token, cached)  # Reuse is not a lease refresh or resurrection.
            return cached
        try:
            payload = self.source.project(selected)
            require(hmac.compare_digest(digest(payload), expected_sha256), 'STALE_READER_VIEW', 409)
            with self._lock:
                require(self._session(token) is session and session.epoch == epoch,
                        'SELECTION_SUPERSEDED', 409)
                now = self.clock.wall_ms()
                expires = min(now + self.lease_seconds * 1000, session.expires_ms)
                ticket = {'schema': 'book.selection-lease.v1', 'issuer_id': self.issuer_id,
                          'session_id': session.public_id, 'epoch': epoch,
                          'lease_id': 'lease-' + secrets.token_hex(16), 'selection': selected.json(),
                          'content_sha256': expected_sha256, 'issued_at_ms': now, 'expires_at_ms': expires}
                ticket['mac'] = hmac.new(self._key, canonical(ticket), hashlib.sha256).hexdigest()
                session.active = deepcopy(ticket)
                session.lease_deadline = min(self.clock.monotonic() + (expires - now) / 1000, session.deadline)
                session.commands[request_id].update(state='complete', result=deepcopy(ticket))
                return deepcopy(ticket)
        except BridgeError as exc:
            with self._lock:
                session.commands[request_id].update(state='failed', code=exc.code, status=exc.status)
            raise
        except Exception:
            with self._lock:
                session.commands[request_id].update(state='failed', code='SOURCE_UNAVAILABLE', status=503)
            raise BridgeError('SOURCE_UNAVAILABLE', 503) from None

    def clear(self, token: str, sequence: int, request_id: str) -> dict:
        self._command(sequence, request_id)
        with self._lock:
            session = self._session(token)
            fp = digest({'op': 'clear', 'sequence': sequence})
            cached = self._begin(session, sequence, request_id, fp)
            if cached is not None:
                return cached
            result = self._status(session)
            session.commands[request_id].update(state='complete', result=result)
            return deepcopy(result)

    def revoke(self, token: str) -> None:
        with self._lock:
            # Repeated revoke is harmless while the instance retains this token.
            session = self._sessions.get(self._token_key(token))
            require(session is not None, 'UNAUTHORIZED', 403)
            session.revoked, session.active = True, None
            session.epoch += 1

    def _ticket(self, session: Session, ticket: dict) -> None:
        fields = {'schema', 'issuer_id', 'session_id', 'epoch', 'lease_id', 'selection',
                  'content_sha256', 'issued_at_ms', 'expires_at_ms', 'mac'}
        require(type(ticket) is dict and set(ticket) == fields, 'INVALID_TICKET')
        require(ticket['schema'] == 'book.selection-lease.v1', 'INVALID_TICKET')
        Selection.parse(ticket['selection'])
        for key in ('issuer_id', 'session_id', 'lease_id'):
            identifier(ticket[key])
        for key in ('epoch', 'issued_at_ms', 'expires_at_ms'):
            require(type(ticket[key]) is int and 0 < ticket[key] <= 2**53 - 1, 'INVALID_TICKET')
        for key in ('content_sha256', 'mac'):
            require(type(ticket[key]) is str and HEX.fullmatch(ticket[key]) is not None, 'INVALID_TICKET')
        unsigned = {k: v for k, v in ticket.items() if k != 'mac'}
        expected = hmac.new(self._key, canonical(unsigned), hashlib.sha256).hexdigest()
        require(hmac.compare_digest(expected, ticket['mac']), 'INVALID_TICKET_MAC', 403)
        require(ticket['issuer_id'] == self.issuer_id and ticket['session_id'] == session.public_id,
                'WRONG_SESSION', 403)
        require(session.active is not None and canonical(session.active) == canonical(ticket)
                and ticket['epoch'] == session.epoch, 'SELECTION_INACTIVE', 409)
        require(ticket['issued_at_ms'] <= self.clock.wall_ms() < ticket['expires_at_ms']
                and self.clock.monotonic() < session.lease_deadline, 'SELECTION_EXPIRED', 409)

    def resolve(self, token: str, ticket: dict) -> dict:
        # Snapshot mutable caller input before any unlocked work.
        ticket = deepcopy(ticket)
        with self._lock:
            session = self._session(token)
            self._ticket(session, ticket)
        payload = self.source.project(Selection.parse(ticket['selection']))
        require(hmac.compare_digest(digest(payload), ticket['content_sha256']), 'SOURCE_CHANGED', 409)
        with self._lock:
            require(self._session(token) is session, 'UNAUTHORIZED', 403)
            self._ticket(session, ticket)
        return payload

    def commit_current(self, token: str, ticket: dict, commit: Callable[[], T]) -> T:
        """Fresh source read then a lease-locked commit; callback must be bounded.

        Revocation before this linearization point prevents publication. It cannot
        retract bytes already delivered. The source directory must be trusted;
        this is not a lock against a malicious local process rewriting files.
        """
        stable = deepcopy(ticket)
        self.resolve(token, stable)
        with self._lock:
            self._ticket(self._session(token), stable)
            return commit()
