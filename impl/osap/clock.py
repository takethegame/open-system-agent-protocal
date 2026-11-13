# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Deadline tracking on a monotonic clock (standard.md §7.8).

`deadline` is an absolute wall-clock instant, but the remaining time is
measured on a monotonic clock, so a wall-clock rollback or a suspend/resume
cycle cannot revive an expired request (§11.1, C0-07).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from .errors import OsapError


def parse_timestamp(value: object) -> datetime:
    """Parse an RFC 3339 timestamp, treating `Z` as UTC."""

    if not isinstance(value, str) or not value:
        raise OsapError("SCHEMA_INVALID", "timestamp must be a non-empty string")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise OsapError("SCHEMA_INVALID", f"malformed timestamp: {value!r}") from None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class Deadline:
    """A deadline whose remaining time only moves forward."""

    def __init__(self, budget_seconds: float, monotonic=None) -> None:
        if budget_seconds < 0:
            raise ValueError("budget_seconds must be non-negative")
        self.budget = float(budget_seconds)
        self._monotonic = monotonic or time.monotonic
        self._started = self._monotonic()

    @classmethod
    def from_envelope(cls, message: dict, monotonic=None) -> "Deadline":
        """Build a deadline from a `request`/`delegate`/`handoff` envelope."""

        issued = parse_timestamp(message.get("ts"))
        due = parse_timestamp(message.get("deadline"))
        return cls((due - issued).total_seconds(), monotonic=monotonic)

    def elapsed(self) -> float:
        return self._monotonic() - self._started

    def remaining(self) -> float:
        return self.budget - self.elapsed()

    def expired(self) -> bool:
        return self.remaining() <= 0

    def check(self) -> None:
        """Raise `TIMEOUT` when the deadline has passed."""

        if self.expired():
            raise OsapError(
                "TIMEOUT",
                "deadline passed on the monotonic clock",
                details={
                    "budget_seconds": self.budget,
                    "elapsed_seconds": round(self.elapsed(), 3),
                },
            )
