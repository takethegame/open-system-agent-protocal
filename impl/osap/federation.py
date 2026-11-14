# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Federation adapters: native descriptors to capability records (§6.7, §6.8).

A Bridge Adapter reads a native descriptor, projects it into a capability
record, and keeps the native identity. The projection in this module is
deliberately read-only: it never mutates the native registry, and it keeps
`source`, `native_id`, `version`, and `provenance` intact (§6.7).

The projection also normalizes trust. Content that arrives over an external
protocol (MCP, A2A, OpenAPI, or a custom bridge) is marked `origin=external`
and cannot claim `system` trust without a verifier this implementation does
not have, so it is reported as `unverified` (§6.4).
"""

from __future__ import annotations

from urllib.parse import quote

from . import schema
from .errors import OsapError

RECORD_SCHEMA = "capability-record.schema.json"

#: Source kinds that cross a device or process boundary (§6.4).
EXTERNAL_KINDS = frozenset({"mcp", "a2a", "openapi", "bridge"})

#: Trust levels from weakest to strongest (§6.4).
TRUST_LEVELS = ("unverified", "verified", "system")


def is_external(kind: str) -> bool:
    """True when a source kind crosses a trust boundary (§6.4)."""

    return kind in EXTERNAL_KINDS


def effective_trust(kind: str, claimed: str) -> str:
    """Keep native trust for local registries and cap external claims (§6.4)."""

    if claimed not in TRUST_LEVELS:
        raise OsapError("SCHEMA_INVALID", f"unknown provenance trust: {claimed!r}")
    if is_external(kind):
        # This adapter does not verify external signatures, so the highest
        # honest level is `unverified`; RFS must never promote it to `system`.
        return "unverified"
    return claimed


def parse_native_id(kind: str, native_id: str) -> dict:
    """Split a native identifier into the fields §6.7 says to preserve."""

    if kind == "mcp":
        server, separator, tool = native_id.partition(":")
        if not separator or not server or not tool:
            raise OsapError("SCHEMA_INVALID", f"MCP native_id must be 'server:tool': {native_id!r}")
        return {"server": server, "tool": tool}

    if kind == "a2a":
        agent_card, separator, skill = native_id.rpartition("#")
        if not separator or not agent_card or not skill:
            raise OsapError("SCHEMA_INVALID", f"A2A native_id must be 'card#skill': {native_id!r}")
        return {"agent_card": agent_card, "skill": skill}

    if kind == "dbus":
        return _parse_dbus(native_id)

    if kind == "openapi":
        return {"operation": native_id}

    return {}


def _parse_dbus(native_id: str) -> dict:
    """Parse `bus:interface:path:interface.method` (the §6.7 D-Bus shape)."""

    parts = native_id.split(":")
    paths = [part for part in parts if part.startswith("/")]
    if len(parts) < 4 or not paths:
        raise OsapError(
            "SCHEMA_INVALID",
            f"D-Bus native_id must be 'bus:interface:path:interface.method': {native_id!r}",
        )

    bus = parts[0]
    path = paths[0]
    tail = parts[-1]
    interfaces = [part for part in parts[1:] if part != path and part != tail]
    interface = interfaces[0] if interfaces else tail.rpartition(".")[0]

    prefix = f"{interface}."
    method = tail[len(prefix):] if tail.startswith(prefix) else tail.rpartition(".")[2]
    if not interface or not method:
        raise OsapError(
            "SCHEMA_INVALID", f"cannot derive the D-Bus interface and method: {native_id!r}"
        )
    return {"bus": bus, "path": path, "interface": interface, "method": method}


def mapped_capability(source: dict) -> str:
    """Return a deterministic OSAP capability name for a native source (§6.8)."""

    registry = source["registry"].replace(".", "-").replace("/", "-")
    native = quote(source["native_id"], safe="")
    return f"cap://federation/{registry}/{native}"


def project(record: dict) -> dict:
    """Project one validated capability record and preserve its native identity."""

    schema.validate(RECORD_SCHEMA, record)
    source = record["source"]
    kind = source["kind"]
    native_id = source["native_id"]

    projection = {
        "record_id": record["record_id"],
        "source_kind": kind,
        "registry": source["registry"],
        "native_id": native_id,
        "version": source.get("version"),
        "origin": "external" if is_external(kind) else "local",
        "trust": effective_trust(kind, record["provenance"]["trust"]),
        "schema": record["capability"]["schemas"][0],
        "capability": record["capability"],
        "mapped_capability": mapped_capability(source),
        "visibility": record["policy"]["visibility"],
    }
    projection.update(parse_native_id(kind, native_id))
    return projection


def refresh(record: dict, *, observed_at: str, expires_at: str) -> dict:
    """Return a copy with a new freshness window after a native refresh (§6.10)."""

    refreshed = dict(record)
    refreshed["freshness"] = {"observed_at": observed_at, "expires_at": expires_at}
    return refreshed
