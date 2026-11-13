# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for consent receipts (standard.md §5.8)."""

import copy
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from osap import OsapError, consent

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"

#: Examples/request.json is stamped 2026-11-10T10:14:45Z.
NOW = datetime(2026, 11, 10, 10, 14, 45, tzinfo=timezone.utc)


def receipt() -> dict:
    return json.loads((EXAMPLES / "consent-receipt.json").read_text(encoding="utf-8"))


def capability() -> dict:
    return json.loads((EXAMPLES / "capability.json").read_text(encoding="utf-8"))


class ConsentValidationTests(unittest.TestCase):
    def test_example_receipt_is_accepted(self):
        validated = consent.validate(receipt(), capability(), now=NOW)
        self.assertEqual(validated["receipt_id"], receipt()["receipt_id"])

    def test_denied_decision_is_rejected(self):
        document = receipt()
        document["decision"] = "deny"
        with self.assertRaises(OsapError) as caught:
            consent.validate(document, capability(), now=NOW)
        self.assertEqual(caught.exception.code, "POLICY_DENIED")

    def test_expired_receipt_is_rejected(self):
        document = receipt()
        document["constraints"]["expires_at"] = "2026-11-10T09:00:00Z"
        with self.assertRaises(OsapError) as caught:
            consent.validate(document, capability(), now=NOW)
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_EXPIRED")

    def test_expiry_wins_over_scope_problems(self):
        document = receipt()
        document["constraints"]["expires_at"] = "2026-11-10T09:00:00Z"
        document["actions"] = ["read"]
        with self.assertRaises(OsapError) as caught:
            consent.validate(document, capability(), now=NOW)
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_EXPIRED")

    def test_receipt_is_accepted_just_before_expiry(self):
        document = receipt()
        document["constraints"]["expires_at"] = "2026-11-10T10:14:46Z"
        consent.validate(document, capability(), now=NOW)

    def test_cap_id_mismatch_is_rejected(self):
        document = receipt()
        document["cap_id"] = "cap_other"
        with self.assertRaises(OsapError) as caught:
            consent.validate(document, capability(), now=NOW)
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_SCOPE_MISMATCH")
        self.assertEqual(caught.exception.details["reason"], "cap_id")

    def test_task_mismatch_is_rejected(self):
        document = receipt()
        document["task_id"] = "task_other"
        with self.assertRaises(OsapError) as caught:
            consent.validate(document, capability(), now=NOW)
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_SCOPE_MISMATCH")
        self.assertEqual(caught.exception.details["reason"], "task_id")

    def test_audience_mismatch_is_rejected(self):
        document = receipt()
        document["audience"] = "agent://com.example.notes/agent#77"
        with self.assertRaises(OsapError) as caught:
            consent.validate(document, capability(), now=NOW)
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_SCOPE_MISMATCH")
        self.assertEqual(caught.exception.details["reason"], "audience")

    def test_agent_mismatch_is_rejected(self):
        document = receipt()
        document["agent"] = "agent://com.example.notes/agent#77"
        with self.assertRaises(OsapError) as caught:
            consent.validate(document, capability(), now=NOW)
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_SCOPE_MISMATCH")
        self.assertEqual(caught.exception.details["reason"], "agent")

    def test_narrower_actions_are_accepted(self):
        document = receipt()
        document["actions"] = ["propose"]
        consent.validate(document, capability(), now=NOW)

    def test_actions_outside_the_capability_are_rejected(self):
        document = receipt()
        document["actions"] = ["read"]
        with self.assertRaises(OsapError) as caught:
            consent.validate(document, capability(), now=NOW)
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_SCOPE_MISMATCH")
        self.assertEqual(caught.exception.details["reason"], "actions")

    def test_resources_outside_the_capability_are_rejected(self):
        document = receipt()
        document["resources"] = ["calendar:work"]
        with self.assertRaises(OsapError) as caught:
            consent.validate(document, capability(), now=NOW)
        self.assertEqual(caught.exception.details["reason"], "resources")

    def test_invalid_receipt_schema_is_rejected(self):
        document = receipt()
        del document["decision"]
        with self.assertRaises(OsapError) as caught:
            consent.validate(document, capability(), now=NOW)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_scope_report(self):
        report = consent.applies_to(receipt(), capability())
        self.assertTrue(all(report.values()))
        wider = copy.deepcopy(receipt())
        wider["actions"] = ["read"]
        self.assertFalse(consent.applies_to(wider, capability())["actions"])


if __name__ == "__main__":
    unittest.main()
