# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Conformance adapter for the reference implementation.

Run with:

    python3 tools/conformance_run.py --impl impl/adapter.py --level C0

M2.1 implements the envelope, the error model, and both framing bindings.
Cases outside that scope return `skip` with the milestone that will pick them
up, so a partial implementation reports honestly instead of failing.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from osap import Bus, Deadline, OsapError, framing  # noqa: E402

MILESTONES = {
    "C1": "M2.2 identity and handshake",
    "C2": "M2.2 registry and discovery",
    "C3": "M2.3 capabilities and M2.4 consent",
    "C4": "M2.5 task model",
    "C5": "M2.5 context fabric",
    "C6": "M2.5 federation",
    "C7": "M2.6 audit chain",
}

DEFAULT_VERSION = "0.1"


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


def conformance_check(case: dict, documents: dict) -> dict:
    level = case.get("level")
    if level != "C0":
        return {
            "outcome": "skip",
            "reason": f"{level} is implemented in {MILESTONES.get(level, 'a later milestone')}",
        }

    operation = case.get("operation")
    params = (case.get("input") or {}).get("params") or {}
    primary = documents.get("primary")

    try:
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
    except OsapError as error:
        return {
            "outcome": "reject",
            "error": error.code,
            "state": {"retryable": error.retryable, "standard_code": error.standard},
        }
    except NotImplementedError as error:
        return {"outcome": "skip", "reason": str(error)}


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
