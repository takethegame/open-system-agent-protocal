# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Minimal Bus core: handshake, envelope validation, routing, idempotency.

Scope is M2.1. Identity, capabilities, consent, and the task model arrive in
later milestones; message types outside this scope raise `NotImplementedError`
so the conformance adapter can report them as `skip` rather than `fail`.
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import envelope, framing
from .clock import Deadline
from .errors import OsapError
from .idempotency import IdempotencyIndex

AWAITING_HELLO = "awaiting_hello"
READY = "ready"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class Bus:
    """A single-user, in-process Bus."""

    def __init__(
        self,
        *,
        binding: framing.Binding = framing.Binding.STREAM,
        version: str = "0.1",
    ) -> None:
        self.binding = binding
        self.version = version
        self.state = AWAITING_HELLO
        self.idempotency = IdempotencyIndex()
        self.side_effects = 0
        self.replays = 0
        self.received: list[str] = []

    # --- lifecycle ---------------------------------------------------------

    def handshake(self, hello: dict) -> dict:
        """Negotiate versions and answer with `welcome` (§7.1, §7.9)."""

        if not isinstance(hello, dict):
            raise OsapError("SCHEMA_INVALID", "hello must be an envelope object")
        version = hello.get("osap")
        if not isinstance(version, str):
            raise OsapError("SCHEMA_INVALID", "hello must carry an osap version")
        if envelope.major_version(version) != envelope.SUPPORTED_MAJOR:
            raise OsapError(
                "TRANSPORT_VERSION_UNSUPPORTED",
                f"unsupported osap major version: {version}",
                details={"supported_major": envelope.SUPPORTED_MAJOR},
            )
        if hello.get("type") not in (None, "hello"):
            raise OsapError("SCHEMA_INVALID", "handshake expects a hello message")
        if hello.get("type") == "hello":
            envelope.validate(hello)

        self.state = READY
        welcome = {
            "osap": self.version,
            "id": f"welcome_{hello.get('id', 'anonymous')}",
            "type": "welcome",
            "from": "agent://system/bus#0",
            "to": {"agent": hello.get("from", "agent://system/bus#0")},
            "body": {
                "schema": "osap.welcome/v1",
                "data": {
                    "osap": self.version,
                    "binding": self.binding.value,
                    "max_frame_bytes": framing.MAX_FRAME_BYTES,
                },
            },
            "ts": _now(),
        }
        if hello.get("id"):
            welcome["causation_id"] = hello["id"]
        return welcome

    # --- receive -----------------------------------------------------------

    def receive(self, message: dict) -> dict:
        """Validate and dispatch one logical message."""

        if self.state == AWAITING_HELLO:
            if not isinstance(message, dict) or message.get("type") != "hello":
                raise OsapError(
                    "TRANSPORT_HANDSHAKE_REQUIRED",
                    "hello/welcome has not completed on this connection",
                )
            return self.handshake(message)

        envelope.validate(message)
        self.received.append(message["id"])
        return self.dispatch(message)

    def receive_bytes(self, data: bytes) -> list[dict]:
        """Decode a stream binding buffer and dispatch every complete frame."""

        if self.binding != framing.Binding.STREAM:
            raise RuntimeError("raw bytes require a stream binding")
        messages, _remainder = framing.decode_stream(data)
        return [self.receive(message) for message in messages]

    def dispatch(self, message: dict) -> dict:
        """Route a validated message."""

        kind = message["type"]
        if kind == "request":
            deadline = Deadline.from_envelope(message)
            deadline.check()

            def execute() -> dict:
                self.side_effects += 1
                return {"status": "accepted", "task_id": envelope.task_id(message)}

            result, replayed = self.idempotency.execute_once(message["id"], execute)
            if replayed:
                self.replays += 1
            return {
                "type": "result",
                "id": message["id"],
                "causation_id": message["id"],
                "replayed": replayed,
                "body": {"schema": "osap.result/v1", "data": result},
            }

        raise NotImplementedError(f"bus does not route {kind!r} before M2.3")

    # --- errors ------------------------------------------------------------

    def error_envelope(self, request: dict, error: OsapError) -> dict:
        """Build the `osap.error/v1` reply for a rejected request."""

        envelope_out = {
            "osap": self.version,
            "id": f"err_{request.get('id', 'unknown')}",
            "type": "error",
            "from": "agent://system/bus#0",
            "to": {"agent": request.get("from", "agent://system/bus#0")},
            "body": {"schema": "osap.error/v1", "data": error.to_data()},
            "ts": _now(),
        }
        if request.get("id"):
            envelope_out["causation_id"] = request["id"]
        if request.get("trace_id"):
            envelope_out["trace_id"] = request["trace_id"]
        return envelope_out
