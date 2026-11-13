# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for the registry subset (standard.md §6.2, §6.6, §6.10)."""

import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from osap import OsapError, crypto, registry

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def record(**overrides) -> dict:
    document = {
        "record_id": "cr_01J9Z6Q3V8N2K4M7P1R5T0WX03",
        "source": {
            "kind": "vendor_registry",
            "registry": "android.appfunctions",
            "native_id": "com.example.calendar.createEvent",
            "version": "1.0.0",
        },
        "app": "app://com.example.calendar",
        "agent": "agent://com.example.calendar/agent#9c",
        "capability": {
            "cap": "cap://os/calendar/events",
            "actions": ["read", "propose", "create"],
            "resources": ["calendar:primary"],
            "schemas": ["osap.calendar.propose/v1", "osap.calendar.proposal/v1"],
            "risk": "L2",
        },
        "policy": {"visibility": "discoverable", "consent": "first_use"},
        "provenance": {
            "trust": "system",
            "signature": "base64url-example",
            "attested_at": "2026-11-10T10:00:00Z",
        },
        "freshness": {
            "observed_at": "2026-11-10T10:00:00Z",
            "expires_at": "2026-11-11T10:00:00Z",
        },
    }
    document.update(overrides)
    return document


class RecordIndexTests(unittest.TestCase):
    def test_fresh_record_is_indexed(self):
        instance = registry.Registry()
        self.assertTrue(instance.index_record(record(), now=datetime(2026, 11, 10, 12, tzinfo=timezone.utc)))

    def test_expired_record_is_not_indexed(self):
        instance = registry.Registry()
        indexed = instance.index_record(record(), now=datetime(2026, 11, 12, tzinfo=timezone.utc))
        self.assertFalse(indexed)
        self.assertEqual(instance.records(), [])

    def test_missing_provenance_is_schema_invalid(self):
        document = record()
        del document["provenance"]
        with self.assertRaises(OsapError) as caught:
            registry.Registry().index_record(document)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_unsigned_manifest_is_denied(self):
        manifest = json.loads((EXAMPLES / "manifest.json").read_text(encoding="utf-8"))
        with self.assertRaises(OsapError) as caught:
            registry.Registry().index_manifest(manifest)
        self.assertEqual(caught.exception.code, "AUTH_DENIED")

    def test_manifest_without_signature_is_schema_invalid(self):
        manifest = json.loads((EXAMPLES / "manifest.json").read_text(encoding="utf-8"))
        del manifest["signature"]
        with self.assertRaises(OsapError) as caught:
            registry.Registry().index_manifest(manifest)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_trusted_signed_manifest_is_indexed(self):
        private, public = crypto.generate_keypair()
        manifest = json.loads((EXAMPLES / "manifest.json").read_text(encoding="utf-8"))
        instance = registry.Registry()
        instance.trust(manifest["app"], public)
        instance.index_manifest(crypto.sign_document(manifest, private))
        self.assertIsNotNone(instance.manifest_for(manifest["app"]))


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.instance = registry.Registry()
        now = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
        self.instance.index_record(record(), now=now)
        self.now = now

    def test_candidate_carries_consent_hint_not_verdict(self):
        candidates = self.instance.discover(
            {"requires": ["calendar.propose"], "schemas": ["osap.calendar.propose/v1"]},
            now=self.now,
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["consent_hint"], "first_use")
        self.assertNotIn("policy_verdict", candidate)
        self.assertFalse(registry.leaks_payload(candidates))
        self.assertFalse(registry.has_live_verdict(candidates))

    def test_risk_ceiling_filters_candidates(self):
        candidates = self.instance.discover({"risk_max": "L1"}, now=self.now)
        self.assertEqual(candidates, [])

    def test_hidden_records_are_not_discovered(self):
        document = record(record_id="cr_hidden")
        document["policy"]["visibility"] = "hidden"
        self.instance.index_record(document, now=self.now)
        candidates = self.instance.discover({"requires": ["calendar.read"]}, now=self.now)
        self.assertEqual([item["record_id"] for item in candidates], ["cr_01J9Z6Q3V8N2K4M7P1R5T0WX03"])

    def test_expired_records_drop_out_of_discovery(self):
        later = self.now + timedelta(days=2)
        self.assertEqual(self.instance.discover({"requires": ["calendar.read"]}, now=later), [])

    def test_payload_leak_is_detected(self):
        self.assertTrue(registry.leaks_payload([{"record_id": "cr_1", "data": {"secret": 1}}]))
        self.assertTrue(registry.has_live_verdict([{"policy_verdict": "allow"}]))


if __name__ == "__main__":
    unittest.main()
