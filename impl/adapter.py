# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Conformance adapter for the reference implementation.

Run with:

    python3 tools/conformance_run.py --impl impl/adapter.py

M2.1 covers the envelope, the error model, and both framing bindings.
M2.2 adds identity, Ed25519-signed manifests, and the registry subset.
Cases outside the implemented scope return `skip` with the milestone that
will pick them up, so a partial implementation reports honestly.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from osap import Bus, Deadline, OsapError, crypto, framing, identity, registry  # noqa: E402

MILESTONES = {
    "C3": "M2.3 capabilities and M2.4 consent",
    "C4": "M2.5 task model",
    "C5": "M2.5 context fabric",
    "C6": "M2.5 federation adapters",
    "C7": "M2.6 audit chain",
}

DEFAULT_VERSION = "0.1"

#: Example public keys are placeholders; the manifests below are signed with a
#: throwaway Ed25519 key generated at import time so real verification runs.
DEV_APP_KEYS = {
    "app://com.example.notes": "base64url-example-public-key",
    "app://com.example.calendar": "base64url-example-public-key",
}

_DEV_REGISTRIES: dict[bool, registry.Registry] = {}


class _FakeMonotonic:
    """A monotonic clock the test can move forward."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _ready_bus(**kwargs) -> Bus:
    bus = Bus(**kwargs)
    bus.handshake({"osap": DEFAULT_VERSION})
    return bus


def _dev_manifest(app: str, agent: str, public_key: str) -> dict:
    capabilities = {
        "app://com.example.notes": [
            {
                "cap": "cap://os/notes/documents",
                "actions": ["read", "write"],
                "resources": ["notes:local"],
                "schemas": ["osap.notes.document/v1"],
                "risk": "L2",
                "consent": "first_use",
            }
        ],
        "app://com.example.calendar": [
            {
                "cap": "cap://os/calendar/events",
                "actions": ["read", "propose", "create"],
                "resources": ["calendar:primary"],
                "schemas": [
                    "osap.calendar.event/v1",
                    "osap.calendar.propose/v1",
                    "osap.calendar.proposal/v1",
                ],
                "risk": "L2",
                "consent": "first_use",
            }
        ],
    }[app]
    return {
        "osap_manifest": DEFAULT_VERSION,
        "app": app,
        "version": "1.0.0",
        "signature": "",
        "agents": [
            {
                "agent": agent,
                "display_name": agent.rsplit("/", 1)[-1],
                "public_key": public_key,
                "capabilities": capabilities,
            }
        ],
    }


def _dev_registry(include_notes: bool = True) -> registry.Registry:
    """Build a registry with dev-signed manifests for the example agents."""

    if include_notes in _DEV_REGISTRIES:
        return _DEV_REGISTRIES[include_notes]

    apps = {}
    if include_notes:
        apps["app://com.example.notes"] = "agent://com.example.notes/assistant#7f3a"
    apps["app://com.example.calendar"] = "agent://com.example.calendar/agent#9c"

    registry_instance = registry.Registry()
    for app, agent in apps.items():
        private, public = crypto.generate_keypair()
        registry_instance.trust(app, public)
        manifest = _dev_manifest(app, agent, DEV_APP_KEYS[app])
        registry_instance.index_manifest(crypto.sign_document(manifest, private))
    _DEV_REGISTRIES[include_notes] = registry_instance
    return registry_instance


def conformance_check(case: dict, documents: dict) -> dict:
    level = case.get("level")
    handler = {"C0": _check_c0, "C1": _check_c1, "C2": _check_c2}.get(level)
    if handler is None:
        return {
            "outcome": "skip",
            "reason": f"{level} is implemented in {MILESTONES.get(level, 'a later milestone')}",
        }

    try:
        return handler(case, documents)
    except OsapError as error:
        return {
            "outcome": "reject",
            "error": error.code,
            "state": {"retryable": error.retryable, "standard_code": error.standard},
        }
    except NotImplementedError as error:
        return {"outcome": "skip", "reason": str(error)}


# --- C0 transport -----------------------------------------------------------


def _check_c0(case: dict, documents: dict) -> dict:
    operation = case.get("operation")
    params = (case.get("input") or {}).get("params") or {}
    primary = documents.get("primary")

    if operation == "handshake":
        return _check_handshake(params)
    if operation == "frame":
        return _check_frame(params)
    if operation == "send":
        return _check_send(primary)
    if operation == "replay":
        return _check_replay(primary, params)
    if operation == "clock":
        return _check_clock(primary, params)
    return {"outcome": "skip", "reason": f"C0 operation {operation!r} has no automated check"}


def _check_handshake(params: dict) -> dict:
    hello = params.get("hello") or {"osap": DEFAULT_VERSION}
    welcome = Bus().handshake(hello)
    return {
        "outcome": "accept",
        "state": {
            "version": welcome["body"]["data"]["osap"],
            "binding": welcome["body"]["data"]["binding"],
        },
    }


def _check_frame(params: dict) -> dict:
    size = framing.check_size(int(params["frame_bytes"]))
    return {"outcome": "accept", "state": {"frame_bytes": size}}


def _check_send(message: dict) -> dict:
    bus = _ready_bus()
    bus.receive(message)
    return {"outcome": "accept", "state": {"routed": True}}


def _check_replay(message: dict, params: dict) -> dict:
    bus = _ready_bus()
    repeat = int(params.get("repeat", 2))
    for _ in range(repeat):
        bus.receive(message)
    return {
        "outcome": "accept",
        "state": {
            "side_effects": bus.side_effects,
            "idempotent_replay": bus.replays > 0 and bus.side_effects == 1,
        },
    }


def _check_clock(message: dict, params: dict) -> dict:
    clock = _FakeMonotonic()
    deadline = Deadline.from_envelope(message, monotonic=clock)
    skew = float(params.get("skew_seconds", 0))
    # A wall-clock implementation would see `deadline.budget - skew` seconds left.
    wall_remaining = deadline.budget - skew
    # Suspend/resume advances the monotonic clock past the deadline.
    clock.now = deadline.budget + 1
    deadline.check()
    return {"outcome": "accept", "state": {"wall_remaining": wall_remaining}}


# --- C1 identity ------------------------------------------------------------


def _check_c1(case: dict, documents: dict) -> dict:
    primary = documents.get("primary")
    params = (case.get("input") or {}).get("params") or {}

    if "osap_manifest" in primary:
        # C1-03 signs a manifest; indexing verifies the signature.
        registry_instance = _dev_registry()
        registry_instance.index_manifest(primary)
        return {"outcome": "accept", "state": {"indexed": True}}

    registered = params.get("registered", True)
    registry_instance = _dev_registry(include_notes=registered)
    if params.get("key_rotated"):
        within_grace = bool(params.get("within_grace_period", False))
        agent = primary["body"]["data"]["agent"]
        registry_instance.mark_rotated(
            agent,
            rotated_at=datetime.now(timezone.utc) - timedelta(hours=1),
            grace_seconds=3600 if within_grace else 0,
        )

    registrar = identity.Registrar(registry_instance)
    welcome = registrar.register(primary)
    return {
        "outcome": "accept",
        "state": {
            "session_id": welcome["session_id"],
            "app": welcome["body"]["data"]["app"],
        },
    }


# --- C2 registry ------------------------------------------------------------


def _check_c2(case: dict, documents: dict) -> dict:
    operation = case.get("operation")
    primary = documents.get("primary")

    if operation == "index":
        return _check_c2_index(primary)
    if operation == "discover":
        return _check_c2_discover(primary)
    return {"outcome": "skip", "reason": f"C2 operation {operation!r} has no automated check"}


def _check_c2_index(document: dict) -> dict:
    registry_instance = _dev_registry()
    if "record_id" in document:
        indexed = registry_instance.index_record(document)
        return {"outcome": "accept", "state": {"indexed": indexed}}

    registry_instance.index_manifest(document)
    return {"outcome": "accept", "state": {"indexed": True}}


def _check_c2_discover(response: dict) -> dict:
    candidates = response["body"]["data"].get("candidates", [])
    consent_hint = all("consent_hint" in candidate for candidate in candidates)
    live_verdict = registry.has_live_verdict(candidates)
    leaked = registry.leaks_payload(candidates)

    if not consent_hint or live_verdict:
        return {
            "outcome": "observe",
            "state": {
                "consent_hint_present": consent_hint,
                "policy_verdict_present": live_verdict,
                "conforming": False,
            },
        }
    return {"outcome": "accept", "state": {"leaked_data": leaked}}
