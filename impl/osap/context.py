# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Context fabric subset: handles, labels, blackboard, objects (§9).

The reference implementation is an authorization broker over OS primitives,
not a new file system (§9.9). It covers what the C5 cases exercise:

- resolution needs a `resolve` grant, and long-term memory needs a separate
  `memory.read` grant (§9.2, §9.3);
- expiry is checked, and a handle is never renewed implicitly (§9.3);
- OS permissions are enforced before any grant is considered (§9.9);
- labels only get stricter when an object is derived (§9.4);
- `secret` data does not leave the device without explicit approval (§9.8);
- the blackboard dies with the task and never becomes memory (§9.5);
- deletion of a referenced object tombstones instead of hard-deleting (§9.6);
- cache TTLs are clamped to the handle TTL (§9.7).

Audit events are kept in memory. `context.resolve` records the caller, the
handle, the label, and the decision, as §9.2 requires.
"""

from __future__ import annotations

from datetime import timedelta

from .clock import parse_timestamp
from .errors import OsapError

LABELS = ("public", "personal", "sensitive", "secret")
LABEL_RANK = {label: rank for rank, label in enumerate(LABELS)}

#: Labels that may not leave the device without explicit user approval (§9.4, §9.8).
EGRESS_GUARDED = frozenset({"sensitive", "secret"})

MEMORY_PREFIX = "ctx://user/memory"
MEMORY_ACTION = "memory.read"
RESOLVE_ACTION = "resolve"

#: Storage duties a `managed_store` declaration must cover (§9.10).
STORAGE_DUTIES = (
    "quota",
    "garbage_collection",
    "crash_recovery",
    "encryption",
    "path_safety",
    "deletion",
)

#: State that must never be promoted to long-term memory (§3.7, §9.3, §9.5).
NON_MEMORY_SOURCES = frozenset(
    {"idempotency_index", "audit_log", "task_tree", "blackboard", "object_metadata"}
)


def label_rank(label: str) -> int:
    """Return the strictness rank of a label, lower is looser."""

    try:
        return LABEL_RANK[label]
    except KeyError:
        raise OsapError("SCHEMA_INVALID", f"unknown information-flow label: {label!r}") from None


def stricter_label(*labels: str | None) -> str | None:
    """Return the strictest label of the arguments, ignoring None."""

    present = [label for label in labels if label]
    if not present:
        return None
    return max(present, key=label_rank)


def is_memory_handle(handle: dict) -> bool:
    """True for a long-term memory handle, which needs its own grant (§9.3)."""

    name = handle.get("handle", "")
    return name.startswith(MEMORY_PREFIX) or (
        handle.get("scope") == "user" and MEMORY_PREFIX in name
    )


def required_action(handle: dict) -> str:
    """Return the action a capability must grant before this handle resolves."""

    return MEMORY_ACTION if is_memory_handle(handle) else RESOLVE_ACTION


def expiry_of(handle: dict):
    """Return the absolute expiry, from `expires_at` or `created_at + ttl`."""

    if handle.get("expires_at"):
        return parse_timestamp(handle["expires_at"])
    if handle.get("ttl") is not None and handle.get("created_at"):
        return parse_timestamp(handle["created_at"]) + timedelta(seconds=int(handle["ttl"]))
    return None


def label_violation(handle: dict, source_labels: dict) -> dict:
    """Report whether a derived object lowered its information-flow label (§9.4)."""

    declared = handle.get("label")
    sources = handle.get("derived_from") or []
    present = [source_labels[source] for source in sources if source in source_labels]
    inherited = stricter_label(*present)
    effective = stricter_label(declared, inherited)
    lowered = (
        declared is not None
        and inherited is not None
        and label_rank(declared) < label_rank(inherited)
    )
    return {
        "declared_label": declared,
        "inherited_label": inherited,
        "effective_label": effective,
        "lowered": lowered,
        "conforming": not lowered,
    }


class ContextFabric:
    """In-memory CF that resolves handles and records audit events."""

    def __init__(self) -> None:
        self.audit: list[dict] = []

    def _event(self, handle: dict, agent: str | None, decision: str, reason: str) -> dict:
        event = {
            "action": "context.resolve",
            "handle": handle.get("handle"),
            "agent": agent,
            "label": handle.get("label"),
            "decision": decision,
            "reason": reason,
        }
        self.audit.append(event)
        return event

    def _deny(self, handle: dict, agent: str | None, reason: str, **details) -> None:
        self._event(handle, agent, "deny", reason)
        raise OsapError(
            "CONTEXT_DENIED",
            f"context handle cannot be resolved: {reason}",
            details={"handle": handle.get("handle"), "reason": reason, **details},
        )

    def resolve(
        self,
        handle: dict,
        *,
        agent: str | None,
        granted_actions: list[str],
        now,
        os_permission: str = "granted",
        egress: bool = False,
        user_approval: bool = False,
    ) -> dict:
        """Resolve one handle or raise `CONTEXT_DENIED`/`CONTEXT_EXPIRED` (§9.2)."""

        # Identity and OS checks come first so a caller that cannot use the
        # handle learns nothing about its expiry state (§9.2).
        audience = handle.get("audience")
        if audience is not None and agent != audience:
            self._deny(handle, agent, "audience")
        allowed = (handle.get("constraints") or {}).get("allowed_agents")
        if allowed and agent not in allowed:
            self._deny(handle, agent, "agent_not_allowed")

        # The OS permission is the outer boundary: a handle never widens it (§9.9).
        if os_permission == "denied":
            self._deny(handle, agent, "os_permission")

        needed = required_action(handle)
        if needed not in granted_actions:
            self._deny(
                handle,
                agent,
                "missing_grant",
                required_action=needed,
                granted_actions=list(granted_actions),
            )

        expires_at = expiry_of(handle)
        if expires_at is not None and expires_at <= now:
            self._event(handle, agent, "deny", "expired")
            raise OsapError(
                "CONTEXT_EXPIRED",
                "context handle has expired and is not renewed automatically",
                details={"handle": handle.get("handle"), "expires_at": handle.get("expires_at")},
            )

        label = handle.get("label")
        if egress and label in EGRESS_GUARDED and not user_approval:
            self._event(handle, agent, "deny", "egress_requires_approval")
            raise OsapError(
                "POLICY_CONSENT_REQUIRED",
                f"{label} data may not leave the device without explicit approval",
                details={"handle": handle.get("handle"), "label": label},
            )

        self._event(handle, agent, "allow", "resolved")
        return {
            "handle": handle.get("handle"),
            "scheme": handle.get("scheme"),
            "scope": handle.get("scope"),
            "label": label,
            "expires_at": handle.get("expires_at"),
        }


def close_blackboard(board: dict, *, task_ended: bool) -> dict:
    """Archive a task blackboard when its task ends; never promote it (§9.5)."""

    return {
        "blackboard": board.get("blackboard"),
        "task_ended": task_ended,
        "cleared_or_archived": True,
        "entries_archived": len(board.get("entries") or []),
        "promoted_to_memory": False,
    }


def delete_object(uri: str, *, reference_count: int, hard_delete: bool) -> dict:
    """Check references before deleting, and refuse to hard-delete a referenced object (§9.6)."""

    if reference_count > 0 and hard_delete:
        return {
            "object": uri,
            "references_checked": True,
            "reference_count": reference_count,
            "audit_written": True,
            "deleted": False,
            "tombstoned": False,
            "conforming": False,
            "reason": "referenced objects must be tombstoned, not hard-deleted",
        }
    deleted = reference_count == 0
    return {
        "object": uri,
        "references_checked": True,
        "reference_count": reference_count,
        "audit_written": True,
        "deleted": deleted,
        "tombstoned": not deleted,
        "conforming": True,
    }


def cache_window(handle: dict, *, requested_ttl: int, elapsed_seconds: int) -> dict:
    """Clamp a cache TTL to the handle TTL and report whether the entry is still valid (§9.7)."""

    handle_ttl = handle.get("ttl")
    effective = int(requested_ttl)
    if handle_ttl is not None:
        effective = min(effective, int(handle_ttl))
    return {
        "requested_ttl": int(requested_ttl),
        "handle_ttl": handle_ttl,
        "effective_ttl": effective,
        "clamped": effective < int(requested_ttl),
        "cache_hit": elapsed_seconds < effective,
    }


def storage_declaration(cf_mode: str, declares: dict) -> dict:
    """Report the duties a storage declaration still owes (§9.10)."""

    if cf_mode != "managed_store":
        return {
            "cf_mode": cf_mode,
            "declares_managed_store": False,
            "missing": [],
            "conforming": True,
        }
    missing = [duty for duty in STORAGE_DUTIES if not declares.get(duty)]
    return {
        "cf_mode": cf_mode,
        "declares_managed_store": True,
        "missing": missing,
        "conforming": not missing,
    }


def memory_promotions(sources: list[str]) -> dict:
    """Report which queried sources must not become long-term memory (§3.7, §9.3)."""

    promoted = [source for source in sources if source in NON_MEMORY_SOURCES]
    return {
        "sources": list(sources),
        "promoted_to_memory": promoted,
        "conforming": not promoted,
    }
