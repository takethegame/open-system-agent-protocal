# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for the audit chain, export, replay, and recovery (§10)."""

import copy
import json
import unittest
from pathlib import Path

from osap import audit
from osap.errors import OsapError

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def chain() -> dict:
    return load("audit-chain.json")


def executed_pair() -> list:
    intent = chain()["events"][2]
    executed = copy.deepcopy(intent)
    executed["audit_id"] = "audit_after_intent"
    executed["action"] = "effect.executed"
    executed["phase"] = "outcome"
    executed["intent_ref"] = intent["audit_id"]
    executed["prev_hash"] = intent["hash"]
    executed["hash"] = "sha256:after"
    return [intent, executed]


class VerifyTests(unittest.TestCase):
    def test_example_chain_is_valid(self):
        self.assertTrue(audit.verify_chain(chain()))

    def test_tampered_prev_hash_is_rejected(self):
        document = chain()
        document["events"][1]["prev_hash"] = "sha256:tampered0000"
        with self.assertRaises(OsapError) as caught:
            audit.verify_chain(document)
        self.assertEqual(caught.exception.code, audit.CHAIN_INVALID)
        self.assertEqual(caught.exception.details["index"], 1)

    def test_foreign_trace_is_rejected(self):
        document = chain()
        document["events"][1]["trace_id"] = "trace_other"
        with self.assertRaises(OsapError) as caught:
            audit.verify_chain(document)
        self.assertEqual(caught.exception.code, audit.CHAIN_INVALID)

    def test_duplicate_audit_id_is_rejected(self):
        document = chain()
        document["events"][1]["audit_id"] = document["events"][0]["audit_id"]
        with self.assertRaises(OsapError) as caught:
            audit.verify_chain(document)
        self.assertEqual(caught.exception.code, audit.CHAIN_INVALID)

    def test_invalid_event_shape_is_schema_invalid(self):
        document = chain()
        del document["events"][0]["target"]
        with self.assertRaises(OsapError) as caught:
            audit.verify_chain(document)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_effect_intent_without_intent_phase_is_schema_invalid(self):
        document = chain()
        document["events"][2]["phase"] = "outcome"
        with self.assertRaises(OsapError) as caught:
            audit.verify_chain(document)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_audit_chain_invalid_is_a_domain_extension(self):
        error = OsapError(audit.CHAIN_INVALID)
        self.assertFalse(error.standard)


class RedactionTests(unittest.TestCase):
    def setUp(self):
        self.document = chain()
        self.report = audit.redact_chain(self.document, salt="export-salt")

    def test_report_keeps_integrity_and_hides_plaintext(self):
        self.assertTrue(self.report["redacted"])
        self.assertTrue(self.report["chain_verified"])
        self.assertFalse(self.report["plaintext_recoverable"])

    def test_commitments_replace_sensitive_fields(self):
        first = self.report["chain"]["events"][1]
        self.assertTrue(first["target"].startswith("sha256:"))
        self.assertTrue(first["consent_receipt_id"].startswith("sha256:"))
        self.assertTrue(first["policy"].startswith("sha256:"))

    def test_context_references_are_committed_individually(self):
        intent = self.report["chain"]["events"][2]
        self.assertEqual(len(intent["context_refs"]), 1)
        self.assertTrue(intent["context_refs"][0].startswith("sha256:"))

    def test_hashes_are_preserved_for_verification(self):
        self.assertTrue(audit.verify_chain(self.report["chain"]))
        self.assertEqual(
            self.report["chain"]["events"][1]["hash"],
            self.document["events"][1]["hash"],
        )

    def test_redaction_does_not_mutate_the_source(self):
        self.assertEqual(self.document["events"][1]["target"], "calendar:primary")

    def test_different_salts_produce_different_commitments(self):
        other = audit.redact_chain(chain(), salt="another-salt")
        self.assertNotEqual(
            self.report["chain"]["events"][1]["target"],
            other["chain"]["events"][1]["target"],
        )

    def test_default_salt_is_unique_per_export(self):
        first = audit.redact_chain(chain())
        second = audit.redact_chain(chain())
        self.assertNotEqual(first["export_salt"], second["export_salt"])

    def test_tampered_chain_is_refused_before_redaction(self):
        document = chain()
        document["events"][1]["prev_hash"] = "sha256:tampered0000"
        with self.assertRaises(OsapError) as caught:
            audit.redact_chain(document)
        self.assertEqual(caught.exception.code, audit.CHAIN_INVALID)


class RecoveryTests(unittest.TestCase):
    def test_intent_without_outcome_is_unknown(self):
        report = audit.recover_effects(chain()["events"])
        self.assertEqual(report["effect_state"], "unknown")
        self.assertTrue(report["alerted"])
        self.assertTrue(report["requires_reconciliation"])

    def test_intent_and_outcome_is_complete(self):
        report = audit.recover_effects(executed_pair())
        self.assertEqual(report["effect_state"], "complete")
        self.assertFalse(report["alerted"])
        self.assertEqual(report["pending_intents"], [])

    def test_multiple_pending_intents_are_all_reported(self):
        extra = copy.deepcopy(chain()["events"][2])
        extra["audit_id"] = "audit_second_intent"
        report = audit.recover_effects([chain()["events"][2], extra])
        self.assertEqual(len(report["pending_intents"]), 2)


class TraceTests(unittest.TestCase):
    def test_single_trace_with_causation_is_complete(self):
        messages = [
            {"id": "msg_1", "trace_id": "trace_1"},
            {"id": "msg_2", "trace_id": "trace_1", "causation_id": "msg_1"},
        ]
        report = audit.trace_complete(messages)
        self.assertTrue(report["complete"])
        self.assertEqual(report["trace_ids"], ["trace_1"])

    def test_missing_causation_breaks_the_trace(self):
        messages = [
            {"id": "msg_1", "trace_id": "trace_1"},
            {"id": "msg_2", "trace_id": "trace_1"},
        ]
        report = audit.trace_complete(messages)
        self.assertFalse(report["complete"])
        self.assertEqual(report["missing_causation"], ["msg_2"])

    def test_two_trace_ids_are_not_a_single_intent(self):
        messages = [
            {"id": "msg_1", "trace_id": "trace_1"},
            {"id": "msg_2", "trace_id": "trace_2", "causation_id": "msg_1"},
        ]
        report = audit.trace_complete(messages)
        self.assertFalse(report["single_trace"])


class CrossUserTests(unittest.TestCase):
    def test_same_user_is_not_cross_user(self):
        report = audit.authorize_cross_user(
            "user://local/example-user", "user://local/example-user", enabled=False
        )
        self.assertFalse(report["cross_user"])
        self.assertTrue(report["allowed"])

    def test_disabled_cross_user_traffic_is_denied(self):
        with self.assertRaises(OsapError) as caught:
            audit.authorize_cross_user(
                "user://local/example-user", "user://local/other-user", enabled=False
            )
        self.assertEqual(caught.exception.code, "POLICY_DENIED")

    def test_enabled_without_both_consents_needs_consent(self):
        with self.assertRaises(OsapError) as caught:
            audit.authorize_cross_user(
                "user://local/example-user", "user://local/other-user", enabled=True
            )
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_REQUIRED")

    def test_enabled_with_both_consents_is_allowed(self):
        report = audit.authorize_cross_user(
            "user://local/example-user",
            "user://local/other-user",
            enabled=True,
            sender_consented=True,
            receiver_consented=True,
        )
        self.assertTrue(report["allowed"])


class ReplayTests(unittest.TestCase):
    def test_replay_runs_the_side_effect_once(self):
        report = audit.replay_effect("key", repeat=2, replay=True)
        self.assertEqual(report["side_effects"], 1)
        self.assertTrue(report["idempotent_replay"])
        self.assertEqual(report["replays"], 1)

    def test_many_replays_still_run_once(self):
        report = audit.replay_effect("key", repeat=5, replay=True)
        self.assertEqual(report["side_effects"], 1)
        self.assertEqual(report["replays"], 4)

    def test_without_replay_every_call_executes(self):
        report = audit.replay_effect("key", repeat=2, replay=False)
        self.assertEqual(report["side_effects"], 2)
        self.assertFalse(report["idempotent_replay"])


class CompromisedBusTests(unittest.TestCase):
    def test_claiming_p0_protection_is_non_conforming(self):
        report = audit.compromised_bus_declaration(
            bus_compromised=True, claims_p0_protection=True
        )
        self.assertFalse(report["conforming"])
        self.assertFalse(report["p0_protection"])
        self.assertTrue(report["p1_required"])

    def test_not_claiming_protection_is_conforming(self):
        report = audit.compromised_bus_declaration(
            bus_compromised=True, claims_p0_protection=False
        )
        self.assertTrue(report["conforming"])


if __name__ == "__main__":
    unittest.main()
