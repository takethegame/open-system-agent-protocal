# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Audit chain, redacted export, replay, and recovery (§10.5–§10.7, §8.11).

The chain check verifies what the fixtures actually contain: each event is a
valid audit event, every event shares the chain trace, and every `prev_hash`
links to the previous `hash`. It does not recompute hashes from event bodies,
because the example hashes are short placeholders and the standard does not
fix a canonical audit encoding.

Redaction replaces target, policy, consent receipt, and context references
with per-export salted commitments. The hash chain stays untouched, so a
verifier can still prove that the chain was not altered and that each
commitment matches the original field, but cannot recover plaintext (§10.6).

`AUDIT_CHAIN_INVALID` is a domain extension: §10.5 requires verification to
fail but defines no audit-specific standard code.
"""

from __future__ import annotations

import copy
import hashlib
import secrets

from . import schema
from .errors import OsapError
from .idempotency import IdempotencyIndex

EVENT_SCHEMA = "audit-event.schema.json"
CHAIN_INVALID = "AUDIT_CHAIN_INVALID"

#: Fields replaced by commitments in a redacted export (§10.6).
REDACTED_FIELDS = ("target", "policy", "consent_receipt_id", "context_refs")

#: Effect events and the phase each must carry (§10.5).
EFFECT_PHASES = {"effect.intent": "intent", "effect.executed": "outcome"}


def verify_chain(chain: dict) -> bool:
    """Verify event schemas, trace consistency, and hash linkage (§10.6)."""

    events = chain.get("events") or []
    trace_id = chain.get("trace_id")
    seen: set[str] = set()

    for index, event in enumerate(events):
        schema.validate(EVENT_SCHEMA, event)

        if event["trace_id"] != trace_id:
            raise OsapError(
                CHAIN_INVALID,
                "audit event does not belong to the chain trace",
                details={
                    "index": index,
                    "trace_id": event["trace_id"],
                    "chain_trace_id": trace_id,
                },
            )
        if event["audit_id"] in seen:
            raise OsapError(
                CHAIN_INVALID,
                "duplicate audit_id in the chain",
                details={"index": index, "audit_id": event["audit_id"]},
            )
        seen.add(event["audit_id"])

        if index == 0:
            continue
        previous = events[index - 1]
        if event["prev_hash"] != previous["hash"]:
            raise OsapError(
                CHAIN_INVALID,
                "audit event does not link to the previous hash",
                details={
                    "index": index,
                    "audit_id": event["audit_id"],
                    "expected": previous["hash"],
                    "actual": event["prev_hash"],
                },
            )

    return True


def _commitment(salt: str, value: str) -> str:
    digest = hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _redact_value(salt: str, value):
    if isinstance(value, list):
        return [_commitment(salt, item) for item in value]
    return _commitment(salt, value)


def redact_chain(chain: dict, *, salt: str | None = None) -> dict:
    """Verify a chain, then replace sensitive fields with salted commitments."""

    verify_chain(chain)
    export_salt = salt or secrets.token_hex(16)
    redacted = copy.deepcopy(chain)
    committed = 0

    for event in redacted["events"]:
        for field in REDACTED_FIELDS:
            if field in event:
                event[field] = _redact_value(export_salt, event[field])
                committed += 1

    return {
        "chain": redacted,
        "export_salt": export_salt,
        "redacted": True,
        "chain_verified": True,
        "plaintext_recoverable": False,
        "redacted_fields": committed,
    }


def recover_effects(events: list) -> dict:
    """Mark an intent without an outcome as unknown and require reconciliation."""

    executed = {event.get("intent_ref") for event in events if event["action"] == "effect.executed"}
    pending = [
        event["audit_id"]
        for event in events
        if event["action"] == "effect.intent" and event["audit_id"] not in executed
    ]
    return {
        "effect_state": "unknown" if pending else "complete",
        "alerted": bool(pending),
        "pending_intents": pending,
        "requires_reconciliation": bool(pending),
    }


def trace_complete(messages: list) -> dict:
    """Check that a multi-hop trace shares one trace_id and links its hops (§10.6)."""

    trace_ids = {message.get("trace_id") for message in messages}
    missing = [
        message["id"]
        for index, message in enumerate(messages)
        if index > 0 and not message.get("causation_id")
    ]
    return {
        "trace_ids": sorted(trace_id for trace_id in trace_ids if trace_id),
        "single_trace": len(trace_ids) == 1,
        "missing_causation": missing,
        "complete": len(trace_ids) == 1 and not missing,
    }


def authorize_cross_user(
    sender_user: str,
    receiver_user: str,
    *,
    enabled: bool,
    sender_consented: bool = False,
    receiver_consented: bool = False,
) -> dict:
    """Allow cross-user traffic only when it is enabled and both sides consent."""

    if sender_user == receiver_user:
        return {"cross_user": False, "allowed": True}

    if not enabled:
        raise OsapError(
            "POLICY_DENIED",
            "cross-user traffic is disabled for this Bus",
            details={"sender_user": sender_user, "receiver_user": receiver_user},
        )
    if not (sender_consented and receiver_consented):
        raise OsapError(
            "POLICY_CONSENT_REQUIRED",
            "both users must consent before cross-user traffic",
            details={
                "sender_user": sender_user,
                "receiver_user": receiver_user,
                "sender_consented": sender_consented,
                "receiver_consented": receiver_consented,
            },
        )
    return {"cross_user": True, "allowed": True}


def replay_effect(idempotency_key: str, *, repeat: int, replay: bool = True) -> dict:
    """Re-run a request without repeating a side effect when replay is on."""

    if not replay:
        return {
            "side_effects": repeat,
            "idempotent_replay": False,
            "replays": 0,
        }

    index = IdempotencyIndex()
    executed = 0

    def side_effect() -> None:
        nonlocal executed
        executed += 1

    for _ in range(repeat):
        index.execute_once(idempotency_key, side_effect)

    return {
        "side_effects": executed,
        "idempotent_replay": executed == 1,
        "replays": repeat - executed,
    }


def compromised_bus_declaration(
    *, bus_compromised: bool, claims_p0_protection: bool
) -> dict:
    """Report whether a 0.1 claim about a compromised Bus is conforming (§3.6, §11.1)."""

    return {
        "bus_compromised": bus_compromised,
        "claims_p0_protection": claims_p0_protection,
        "p0_protection": False,
        "p1_required": True,
        "conforming": not claims_p0_protection,
    }
