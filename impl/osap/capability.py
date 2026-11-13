# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Capability tokens, attenuation, binding, and revocation (standard.md §5).

Scope is M2.3: issuance bookkeeping, the attenuation rules from §5.3, the
binding checks from §5.4, revocation with cascade, and the consent linkage
required for L3/L4 actions. Token proofs are structurally validated but not
cryptographically verified: issuer key distribution is not part of M2.3.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from . import schema
from .clock import parse_timestamp
from .errors import OsapError

CAPABILITY_SCHEMA = "capability.schema.json"

HIGH_RISK = frozenset({"L3", "L4"})

_RATE = re.compile(r"^(?P<count>\d+)/(?P<period>s|min|hour|day)$")
_PERIOD_MINUTES = {"s": 1 / 60, "min": 1.0, "hour": 60.0, "day": 1440.0}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def rate_per_minute(value: str) -> float | None:
    """Convert `5/min`, `100/hour`, or `1/s` to a per-minute rate."""

    match = _RATE.match(value or "")
    if not match:
        return None
    return int(match["count"]) / _PERIOD_MINUTES[match["period"]]


def _budget_violations(child: dict, parent: dict) -> list[str]:
    violations = []
    child_budget = child.get("max_budget") or {}
    parent_budget = parent.get("max_budget") or {}
    for key in ("wall_ms", "tool_calls", "tokens"):
        if key in parent_budget:
            # Omitting a bounded dimension leaves it unbounded, which widens.
            if key not in child_budget or child_budget[key] > parent_budget[key]:
                violations.append(f"max_budget.{key}")
    if "money" in parent_budget:
        parent_money = parent_budget["money"]
        child_money = child_budget.get("money")
        if child_money is None:
            violations.append("max_budget.money")
        elif child_money.get("currency") != parent_money.get("currency"):
            violations.append("max_budget.money.currency")
        elif child_money.get("amount", 0) > parent_money.get("amount", 0):
            violations.append("max_budget.money")
    return violations


def attenuation_violations(parent: dict, child: dict) -> list[str]:
    """Return every §5.3 rule the requested child breaks."""

    violations: list[str] = []

    if not set(child["actions"]) <= set(parent["actions"]):
        violations.append("actions")
    if not set(child["resources"]) <= set(parent["resources"]):
        violations.append("resources")

    if child["exp"] > parent["exp"]:
        violations.append("exp")
    if child["nbf"] < parent["nbf"]:
        violations.append("nbf")

    parent_limits = parent.get("constraints") or {}
    child_limits = child.get("constraints") or {}

    parent_uses = parent_limits.get("max_uses")
    child_uses = child_limits.get("max_uses")
    if parent_uses is not None and (child_uses is None or child_uses > parent_uses):
        violations.append("constraints.max_uses")

    parent_rate = parent_limits.get("rate")
    child_rate = child_limits.get("rate")
    if parent_rate is not None:
        allowed = rate_per_minute(parent_rate)
        requested = rate_per_minute(child_rate) if child_rate else None
        if requested is None or (allowed is not None and requested > allowed):
            violations.append("constraints.rate")

    violations.extend(_budget_violations(child_limits, parent_limits))

    expected_depth = int(parent.get("depth", 0)) + 1
    if child["depth"] != expected_depth:
        violations.append("depth")
    max_depth = parent_limits.get("max_depth")
    if max_depth is not None and child["depth"] > max_depth:
        violations.append("constraints.max_depth")

    if not parent_limits.get("can_delegate", False):
        violations.append("constraints.can_delegate")

    parent_receipt = parent.get("consent_receipt_id")
    if parent_receipt and child.get("consent_receipt_id") != parent_receipt:
        violations.append("consent_receipt_id")

    return violations


def validate_token(token: dict) -> dict:
    """Validate one capability token against the schema (§5.2)."""

    schema.validate(CAPABILITY_SCHEMA, token)
    return token


def attenuate(parent: dict, requested: dict) -> dict:
    """Return `requested` as a child token, or raise `CAPABILITY_ATTENUATION_INVALID`."""

    schema.validate(CAPABILITY_SCHEMA, parent)
    schema.validate(CAPABILITY_SCHEMA, requested)
    violations = attenuation_violations(parent, requested)
    if violations:
        raise OsapError(
            "CAPABILITY_ATTENUATION_INVALID",
            "child capability widens its parent",
            details={"violations": violations},
        )
    return requested


class CapabilityAuthority:
    """In-memory CA: issuance, revocation with cascade, and use checks."""

    def __init__(self, *, clock=None) -> None:
        self._clock = clock or _now
        self.issued: dict[str, dict] = {}
        self.revoked: set[str] = set()
        self.audit: list[dict] = []

    def issue(self, token: dict) -> dict:
        validate_token(token)
        self.issued[token["cap_id"]] = token
        return token

    def revoke(self, cap_id: str) -> int:
        """Revoke `cap_id` and every descendant; return the number revoked."""

        self.revoked.add(cap_id)
        self.audit.append({"action": "capability.revoked", "target": cap_id})
        count = 1
        changed = True
        while changed:
            changed = False
            for token in self.issued.values():
                parent = token.get("parent_cap_id")
                if parent in self.revoked and token["cap_id"] not in self.revoked:
                    self.revoked.add(token["cap_id"])
                    self.audit.append({"action": "capability.revoked", "target": token["cap_id"]})
                    count += 1
                    changed = True
        return count

    def is_revoked(self, token: dict) -> bool:
        cap_id = token.get("cap_id")
        if cap_id in self.revoked:
            return True
        seen = set()
        parent = token.get("parent_cap_id")
        while parent and parent not in seen:
            if parent in self.revoked:
                return True
            seen.add(parent)
            ancestor = self.issued.get(parent)
            parent = ancestor.get("parent_cap_id") if ancestor else None
        return False

    # --- use checks --------------------------------------------------------

    def check_binding(self, token: dict, envelope: dict, *, audience: str) -> None:
        """Stateless binding rules the Bus can check before routing (§5.4)."""

        if token["audience"] != audience:
            raise OsapError(
                "CAPABILITY_AUDIENCE_MISMATCH",
                "capability audience is not the receiving agent",
                details={"audience": token["audience"], "receiver": audience},
            )
        task = envelope.get("task") or {}
        if token["task_id"] != task.get("id"):
            raise OsapError(
                "CAPABILITY_TASK_MISMATCH",
                "capability task does not match the envelope task",
                details={"capability_task": token["task_id"], "envelope_task": task.get("id")},
            )
        if token["subject"] != envelope.get("from"):
            raise OsapError(
                "CAPABILITY_SUBJECT_MISMATCH",
                "capability subject is not the envelope sender",
                details={"subject": token["subject"], "sender": envelope.get("from")},
            )

    def check_validity(self, token: dict, *, now: datetime | None = None) -> None:
        """Temporal and revocation checks the receiver runs before executing."""

        moment = now or self._clock()
        if self.is_revoked(token):
            raise OsapError("CAPABILITY_REVOKED", "capability or an ancestor is revoked")

        not_before = datetime.fromtimestamp(token["nbf"], tz=timezone.utc)
        expires = datetime.fromtimestamp(token["exp"], tz=timezone.utc)
        if moment < not_before:
            raise OsapError("CAPABILITY_REVOKED", "capability is not valid yet")
        if moment >= expires:
            raise OsapError("CAPABILITY_REVOKED", "capability has expired")

        window = (token.get("constraints") or {}).get("time_window")
        if window:
            start, end = (parse_timestamp(item) for item in window)
            if not start <= moment <= end:
                raise OsapError("CAPABILITY_REVOKED", "capability is outside its time window")

    def require_consent(self, token: dict, *, risk: str | None) -> None:
        """L3/L4 actions must reference a consent receipt (§5.2, §5.8)."""

        if risk in HIGH_RISK and not token.get("consent_receipt_id"):
            raise OsapError(
                "POLICY_CONSENT_REQUIRED",
                f"{risk} actions require a consent receipt",
                details={"risk": risk},
            )
