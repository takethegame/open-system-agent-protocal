# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Registry federation subset (standard.md §6.1–§6.10).

The reference implementation covers what M2.2 needs:

- indexing an app manifest only after its signature verifies (§6.1);
- indexing a capability record only when its schema is valid and it is not
  expired (§6.2, §6.10);
- discovery candidates that carry a static `consent_hint` and never a live
  `policy_verdict` (§6.6, §6.9).

External registry adapters (§6.7) and namespace mapping (§6.8) are out of
scope until a bridge milestone.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import crypto, identity, schema
from .clock import parse_timestamp
from .errors import OsapError

MANIFEST_SCHEMA = "manifest.schema.json"
RECORD_SCHEMA = "capability-record.schema.json"

#: Candidate fields that would leak payload data (§6.6).
PRIVATE_CANDIDATE_KEYS = frozenset({"data", "body", "content"})

RISK_ORDER = {f"L{level}": level for level in range(5)}


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Registry:
    """In-memory RFS holding verified manifests and fresh capability records."""

    def __init__(self, trust_store: dict[str, str] | None = None) -> None:
        self._trust: dict[str, str] = dict(trust_store or {})
        self._manifests: dict[str, dict] = {}
        self._records: dict[str, dict] = {}
        self._rotations: dict[str, tuple[datetime, int]] = {}

    # --- trust -------------------------------------------------------------

    def trust(self, app: str, public_key_b64: str) -> None:
        """Pin the key that signs `app`'s manifest."""

        self._trust[app] = public_key_b64

    def trusted_key(self, app: str) -> str | None:
        return self._trust.get(app)

    # --- manifests ---------------------------------------------------------

    def index_manifest(self, manifest: dict) -> dict:
        """Validate and verify a manifest before indexing it (§6.1)."""

        schema.validate(MANIFEST_SCHEMA, manifest)
        self.require_manifest_signature(manifest)
        self._manifests[manifest["app"]] = manifest
        return manifest

    def require_manifest_signature(self, manifest: dict) -> None:
        app = manifest.get("app")
        if not isinstance(app, str):
            raise OsapError("SCHEMA_INVALID", "manifest.app is required")
        crypto.require_verified(manifest, self._trust.get(app), what="app manifest")

    def manifest_for(self, app: str) -> dict | None:
        return self._manifests.get(app)

    def agent_entry(self, agent: str) -> dict | None:
        manifest = self._manifests.get(identity.app_of_agent(agent))
        if manifest is None:
            return None
        for entry in manifest.get("agents", []):
            if entry.get("agent") == agent:
                return entry
        return None

    # --- key rotation ------------------------------------------------------

    def mark_rotated(self, agent: str, *, rotated_at: datetime | None = None, grace_seconds: int = 0) -> None:
        """Record a key rotation; the old key stays usable during the grace window."""

        self._rotations[agent] = (rotated_at or _now(), int(grace_seconds))

    def key_usable(self, agent: str, *, at: datetime | None = None) -> bool:
        rotation = self._rotations.get(agent)
        if rotation is None:
            return True
        rotated_at, grace_seconds = rotation
        return (at or _now()) <= rotated_at + timedelta(seconds=grace_seconds)

    # --- capability records ------------------------------------------------

    def index_record(self, record: dict, *, now: datetime | None = None) -> bool:
        """Index a record when valid and fresh; return whether it was indexed."""

        schema.validate(RECORD_SCHEMA, record)
        if not self._fresh(record, now):
            return False
        self._records[record["record_id"]] = record
        return True

    def _fresh(self, record: dict, now: datetime | None = None) -> bool:
        expires_at = parse_timestamp(record["freshness"]["expires_at"])
        return expires_at > (now or _now())

    def records(self) -> list[dict]:
        return list(self._records.values())

    # --- discovery ---------------------------------------------------------

    def discover(self, query: dict, *, now: datetime | None = None) -> list[dict]:
        """Return candidates for an `osap.discover/v1` query (§6.5, §6.6)."""

        requires = query.get("requires") or []
        schemas = query.get("schemas") or []
        risk_max = query.get("risk_max")
        sources = query.get("sources")
        limit = int(query.get("limit", 5))

        candidates = []
        for record in self._records.values():
            if not self._fresh(record, now):
                continue
            if record["policy"]["visibility"] != "discoverable":
                continue
            if sources and record["source"]["kind"] not in sources:
                continue
            capability = record["capability"]
            if risk_max and RISK_ORDER[capability["risk"]] > RISK_ORDER[risk_max]:
                continue
            score = self._match(record, requires, schemas)
            if score == 0:
                continue
            candidates.append(self._candidate(record, score))

        candidates.sort(key=lambda item: item["match"], reverse=True)
        return candidates[:limit]

    @staticmethod
    def _match(record: dict, requires: list[str], schemas: list[str]) -> float:
        capability = record["capability"]
        wanted_actions = {item.split(".", 1)[-1] for item in requires} & set(capability["actions"])
        wanted_schemas = set(schemas) & set(capability["schemas"])
        if not wanted_actions and not wanted_schemas:
            return 0.0
        total = max(len(requires) + len(schemas), 1)
        return round((len(wanted_actions) + len(wanted_schemas)) / total, 2)

    @staticmethod
    def _candidate(record: dict, score: float) -> dict:
        return {
            "record_id": record["record_id"],
            "agent": record["agent"],
            "capability": record["capability"]["cap"],
            "match": score,
            "risk": record["capability"]["risk"],
            # Static policy hint, never a live verdict (§6.6).
            "consent_hint": record["policy"]["consent"],
            "source": {
                "kind": record["source"]["kind"],
                "registry": record["source"]["registry"],
            },
            "trust": record["provenance"]["trust"],
            "schemas": list(record["capability"]["schemas"]),
        }


def leaks_payload(candidates: list[dict]) -> bool:
    """True when a candidate carries a payload field (§6.6)."""

    return any(PRIVATE_CANDIDATE_KEYS & set(candidate) for candidate in candidates)


def has_live_verdict(candidates: list[dict]) -> bool:
    """True when a candidate carries a live `policy_verdict` (§6.6, §6.9)."""

    return any("policy_verdict" in candidate for candidate in candidates)
