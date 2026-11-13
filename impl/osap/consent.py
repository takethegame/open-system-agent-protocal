# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Consent receipts and their linkage to capabilities (standard.md §5.8).

A receipt is the record of one user decision. Its scope MUST cover the
capability it is attached to: same `cap_id`, same task, same audience, and
`actions`/`resources` that are subsets of what the capability allows.

The checks run in a fixed order so a caller sees the most specific failure:

1. `decision` must be `grant`;
2. the receipt must not be expired;
3. `cap_id`, `task_id`, and `audience` must match the capability, and
   `agent` must be the capability subject;
4. `actions` and `resources` must be subsets of the capability's.

Steps 3 and 4 report `POLICY_CONSENT_SCOPE_MISMATCH`; they describe what the
user agreed to, not whether the token itself is valid.
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import schema
from .clock import parse_timestamp
from .errors import OsapError

RECEIPT_SCHEMA = "consent-receipt.schema.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _mismatch(reason: str, **details) -> OsapError:
    return OsapError(
        "POLICY_CONSENT_SCOPE_MISMATCH",
        f"consent receipt does not cover the capability: {reason}",
        details={"reason": reason, **details},
    )


def applies_to(receipt: dict, capability: dict) -> dict:
    """Return a scope report without raising, for tests and diagnostics."""

    receipt_actions = set(receipt.get("actions") or [])
    receipt_resources = set(receipt.get("resources") or [])
    return {
        "cap_id": receipt.get("cap_id") == capability.get("cap_id"),
        "task_id": receipt.get("task_id") == capability.get("task_id"),
        "audience": receipt.get("audience") == capability.get("audience"),
        "actions": receipt_actions <= set(capability.get("actions") or []),
        "resources": receipt_resources <= set(capability.get("resources") or []),
    }


def validate(
    receipt: dict,
    capability: dict,
    *,
    now: datetime | None = None,
) -> dict:
    """Validate a receipt against the capability it is attached to (§5.8)."""

    schema.validate(RECEIPT_SCHEMA, receipt)

    if receipt["decision"] != "grant":
        raise OsapError(
            "POLICY_DENIED",
            f"consent decision is {receipt['decision']!r}",
            details={"receipt_id": receipt["receipt_id"]},
        )

    moment = now or _now()
    expires_at = (receipt.get("constraints") or {}).get("expires_at")
    if expires_at and parse_timestamp(expires_at) <= moment:
        raise OsapError(
            "POLICY_CONSENT_EXPIRED",
            "consent receipt has expired",
            details={"receipt_id": receipt["receipt_id"], "expires_at": expires_at},
        )

    if receipt["cap_id"] != capability["cap_id"]:
        raise _mismatch(
            "cap_id",
            receipt_cap_id=receipt["cap_id"],
            capability_cap_id=capability["cap_id"],
        )
    if receipt["task_id"] != capability["task_id"]:
        raise _mismatch(
            "task_id",
            receipt_task_id=receipt["task_id"],
            capability_task_id=capability["task_id"],
        )
    if receipt["audience"] != capability["audience"]:
        raise _mismatch(
            "audience",
            receipt_audience=receipt["audience"],
            capability_audience=capability["audience"],
        )
    if receipt["agent"] != capability["subject"]:
        raise _mismatch(
            "agent",
            receipt_agent=receipt["agent"],
            capability_subject=capability["subject"],
        )

    if not set(receipt["actions"]) <= set(capability["actions"]):
        raise _mismatch(
            "actions",
            receipt_actions=list(receipt["actions"]),
            capability_actions=list(capability["actions"]),
        )
    if not set(receipt["resources"]) <= set(capability["resources"]):
        raise _mismatch(
            "resources",
            receipt_resources=list(receipt["resources"]),
            capability_resources=list(capability["resources"]),
        )
    return receipt
