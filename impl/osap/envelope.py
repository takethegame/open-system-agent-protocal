# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Envelope validation from standard.md §7.1.

The JSON Schema in `schemas/envelope.schema.json` covers shape. This module
adds the ordering the standard requires but a schema cannot express:

1. `osap` must be present and major-compatible;
2. `type` must be one of the known message types;
3. everything else must satisfy the schema.

Step 2 runs before the schema so an unknown type reports `SCHEMA_UNSUPPORTED`
(§7.9) instead of the generic `SCHEMA_INVALID`.
"""

from __future__ import annotations

from . import schema
from .errors import OsapError

SUPPORTED_MAJOR = 0

#: Message types from standard.md §7.2.
KNOWN_TYPES = frozenset(
    {
        "hello",
        "welcome",
        "discover",
        "describe",
        "request",
        "result",
        "error",
        "event",
        "stream.open",
        "stream.chunk",
        "stream.close",
        "cancel",
        "delegate",
        "handoff",
        "status",
        "consent.request",
        "consent.grant",
        "consent.deny",
    }
)

#: Types that must carry a task, a capability, and a deadline (§7.3).
TASK_SCOPED_TYPES = frozenset({"request", "delegate", "handoff"})

ROUTE_KEYS = frozenset({"agent", "capability", "user"})


def major_version(version: str) -> int:
    """Return the major component of an `osap` version, e.g. `0` for `0.1`."""

    try:
        return int(version.split(".", 1)[0])
    except (AttributeError, ValueError):
        raise OsapError("SCHEMA_INVALID", f"malformed osap version: {version!r}") from None


def validate(message: object) -> dict:
    """Validate one envelope, returning it unchanged or raising `OsapError`."""

    if not isinstance(message, dict):
        raise OsapError("SCHEMA_INVALID", "envelope must be a JSON object")

    if "osap" not in message:
        raise OsapError("SCHEMA_INVALID", "osap version is required")
    version = message["osap"]
    if not isinstance(version, str):
        raise OsapError("SCHEMA_INVALID", "osap version must be a string")
    if major_version(version) != SUPPORTED_MAJOR:
        raise OsapError(
            "TRANSPORT_VERSION_UNSUPPORTED",
            f"unsupported osap major version: {version}",
            details={"supported_major": SUPPORTED_MAJOR},
        )

    if "type" not in message:
        raise OsapError("SCHEMA_INVALID", "type is required")
    message_type = message["type"]
    if message_type not in KNOWN_TYPES:
        raise OsapError(
            "SCHEMA_UNSUPPORTED",
            f"unknown message type: {message_type!r}",
            details={"known_types": sorted(KNOWN_TYPES)},
        )

    schema.validate("envelope.schema.json", message)
    return message


def route_kind(message: dict) -> str:
    """Return `agent`, `capability`, or `user` from the `to` object."""

    target = message.get("to")
    if not isinstance(target, dict) or len(target) != 1:
        raise OsapError("SCHEMA_INVALID", "to must hold exactly one route key")
    kind = next(iter(target))
    if kind not in ROUTE_KEYS:
        raise OsapError("SCHEMA_INVALID", f"unsupported route key: {kind!r}")
    return kind


def sender(message: dict) -> str:
    return message["from"]


def task_id(message: dict) -> str | None:
    task = message.get("task")
    return task.get("id") if isinstance(task, dict) else None
