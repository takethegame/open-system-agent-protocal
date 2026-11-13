# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for capability tokens (standard.md §5.2–§5.6)."""

import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from osap import OsapError, capability

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"

PARENT_ID = "cap_01J9Z6Q3V8N2K4M7P1R5T0WXAA"
CHILD_ID = "cap_01J9Z6Q3V8N2K4M7P1R5T0WXAB"
ORCHESTRATOR = "agent://com.example.orchestrator/main#1a2b"
CALENDAR = "agent://com.example.calendar/agent#9c"
TASK = "task_01J9Z6Q3V8N2K4M7P1R5T0WXAB"
# exp inside examples/capability.json is 2026-11-10T11:14:45Z.
VALID_AT = datetime(2026, 11, 10, 10, 14, 45, tzinfo=timezone.utc)


def token() -> dict:
    return json.loads((EXAMPLES / "capability.json").read_text(encoding="utf-8"))


def envelope() -> dict:
    return json.loads((EXAMPLES / "request.json").read_text(encoding="utf-8"))


def parent() -> dict:
    document = token()
    document["cap_id"] = PARENT_ID
    document["depth"] = 0
    return document


def child(**constraints) -> dict:
    document = token()
    if constraints:
        document["constraints"] = {**document["constraints"], **constraints}
    return document


class AttenuationTests(unittest.TestCase):
    def assert_rejected(self, requested: dict, dimension: str) -> None:
        with self.assertRaises(OsapError) as caught:
            capability.attenuate(parent(), requested)
        self.assertEqual(caught.exception.code, "CAPABILITY_ATTENUATION_INVALID")
        self.assertIn(dimension, caught.exception.details["violations"])

    def test_identity_child_is_accepted(self):
        self.assertEqual(capability.attenuate(parent(), child())["cap_id"], CHILD_ID)

    def test_narrowing_actions_is_accepted(self):
        requested = child()
        requested["actions"] = ["propose"]
        capability.attenuate(parent(), requested)

    def test_widening_actions_is_rejected(self):
        requested = child()
        requested["actions"] = ["propose", "create"]
        self.assert_rejected(requested, "actions")

    def test_widening_resources_is_rejected(self):
        requested = child()
        requested["resources"] = ["calendar:primary", "calendar:work"]
        self.assert_rejected(requested, "resources")

    def test_extending_exp_is_rejected(self):
        requested = child()
        requested["exp"] = parent()["exp"] + 1
        self.assert_rejected(requested, "exp")

    def test_shortening_exp_is_accepted(self):
        requested = child()
        requested["exp"] = parent()["exp"] - 1
        capability.attenuate(parent(), requested)

    def test_moving_nbf_earlier_is_rejected(self):
        requested = child()
        requested["nbf"] = parent()["nbf"] - 1
        self.assert_rejected(requested, "nbf")

    def test_raising_max_uses_is_rejected(self):
        self.assert_rejected(child(max_uses=6), "constraints.max_uses")

    def test_dropping_max_uses_is_rejected(self):
        requested = token()
        del requested["constraints"]["max_uses"]
        self.assert_rejected(requested, "constraints.max_uses")

    def test_lowering_max_uses_is_accepted(self):
        capability.attenuate(parent(), child(max_uses=1))

    def test_faster_rate_is_rejected(self):
        self.assert_rejected(child(rate="10/min"), "constraints.rate")

    def test_slower_rate_is_accepted(self):
        capability.attenuate(parent(), child(rate="1/min"))
        capability.attenuate(parent(), child(rate="6/hour"))

    def test_wider_budget_is_rejected(self):
        requested = child()
        requested["constraints"]["max_budget"] = {"wall_ms": 6000, "tool_calls": 2}
        self.assert_rejected(requested, "max_budget.wall_ms")

    def test_dropping_a_budget_dimension_is_rejected(self):
        requested = child()
        requested["constraints"]["max_budget"] = {"tool_calls": 2}
        self.assert_rejected(requested, "max_budget.wall_ms")

    def test_narrower_budget_is_accepted(self):
        requested = child()
        requested["constraints"]["max_budget"] = {"wall_ms": 1000, "tool_calls": 1}
        capability.attenuate(parent(), requested)

    def test_wrong_depth_is_rejected(self):
        requested = token()
        requested["depth"] = 3
        self.assert_rejected(requested, "depth")

    def test_depth_beyond_max_depth_is_rejected(self):
        ancestor = parent()
        ancestor["depth"] = 2
        requested = copy.deepcopy(ancestor)
        requested["cap_id"] = "cap_child"
        requested["depth"] = 3
        with self.assertRaises(OsapError) as caught:
            capability.attenuate(ancestor, requested)
        self.assertIn("constraints.max_depth", caught.exception.details["violations"])

    def test_delegation_must_be_allowed(self):
        ancestor = parent()
        ancestor["constraints"]["can_delegate"] = False
        with self.assertRaises(OsapError) as caught:
            capability.attenuate(ancestor, child())
        self.assertIn("constraints.can_delegate", caught.exception.details["violations"])

    def test_consent_receipt_must_survive(self):
        requested = child()
        requested["consent_receipt_id"] = "consent_other"
        self.assert_rejected(requested, "consent_receipt_id")

    def test_invalid_child_schema_is_rejected(self):
        requested = child()
        del requested["proof"]
        with self.assertRaises(OsapError) as caught:
            capability.attenuate(parent(), requested)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_rate_conversion(self):
        self.assertEqual(capability.rate_per_minute("5/min"), 5.0)
        self.assertEqual(capability.rate_per_minute("60/hour"), 1.0)
        self.assertEqual(capability.rate_per_minute("1/s"), 60.0)
        self.assertIsNone(capability.rate_per_minute("fast"))


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.authority = capability.CapabilityAuthority()

    def test_matching_binding_is_accepted(self):
        self.authority.check_binding(token(), envelope(), audience=CALENDAR)

    def test_audience_mismatch_is_rejected(self):
        with self.assertRaises(OsapError) as caught:
            self.authority.check_binding(
                token(), envelope(), audience="agent://com.example.notes/agent#77"
            )
        self.assertEqual(caught.exception.code, "CAPABILITY_AUDIENCE_MISMATCH")

    def test_task_mismatch_is_rejected(self):
        message = envelope()
        message["task"]["id"] = "task_other"
        with self.assertRaises(OsapError) as caught:
            self.authority.check_binding(token(), message, audience=CALENDAR)
        self.assertEqual(caught.exception.code, "CAPABILITY_TASK_MISMATCH")

    def test_subject_mismatch_is_rejected(self):
        message = envelope()
        message["from"] = "agent://com.example.notes/agent#77"
        with self.assertRaises(OsapError) as caught:
            self.authority.check_binding(token(), message, audience=CALENDAR)
        self.assertEqual(caught.exception.code, "CAPABILITY_SUBJECT_MISMATCH")

    def test_audience_is_checked_before_the_task(self):
        message = envelope()
        message["task"]["id"] = "task_other"
        with self.assertRaises(OsapError) as caught:
            self.authority.check_binding(
                token(), message, audience="agent://com.example.notes/agent#77"
            )
        self.assertEqual(caught.exception.code, "CAPABILITY_AUDIENCE_MISMATCH")


class ValidityTests(unittest.TestCase):
    def setUp(self):
        self.authority = capability.CapabilityAuthority()

    def test_token_is_valid_inside_its_window(self):
        self.authority.check_validity(token(), now=VALID_AT)

    def test_expired_token_is_rejected(self):
        with self.assertRaises(OsapError) as caught:
            self.authority.check_validity(token(), now=VALID_AT + timedelta(hours=2))
        self.assertEqual(caught.exception.code, "CAPABILITY_REVOKED")

    def test_not_yet_valid_token_is_rejected(self):
        with self.assertRaises(OsapError) as caught:
            self.authority.check_validity(token(), now=VALID_AT - timedelta(seconds=1))
        self.assertEqual(caught.exception.code, "CAPABILITY_REVOKED")

    def test_outside_time_window_is_rejected(self):
        with self.assertRaises(OsapError) as caught:
            self.authority.check_validity(token(), now=datetime(2026, 11, 18, tzinfo=timezone.utc))
        self.assertEqual(caught.exception.code, "CAPABILITY_REVOKED")

    def test_revoked_token_is_rejected(self):
        self.authority.revoke(CHILD_ID)
        with self.assertRaises(OsapError) as caught:
            self.authority.check_validity(token(), now=VALID_AT)
        self.assertEqual(caught.exception.code, "CAPABILITY_REVOKED")


class RevocationTests(unittest.TestCase):
    def setUp(self):
        self.authority = capability.CapabilityAuthority()
        self.ancestor = parent()
        self.ancestor["cap_id"] = PARENT_ID
        self.middle = token()
        self.middle["cap_id"] = "cap_middle"
        self.middle["parent_cap_id"] = PARENT_ID
        self.leaf = token()
        self.leaf["cap_id"] = "cap_leaf"
        self.leaf["parent_cap_id"] = "cap_middle"
        for item in (self.ancestor, self.middle, self.leaf):
            self.authority.issue(item)

    def test_revoking_a_parent_cascades_to_descendants(self):
        self.assertEqual(self.authority.revoke(PARENT_ID), 3)
        for item in (self.ancestor, self.middle, self.leaf):
            self.assertTrue(self.authority.is_revoked(item))

    def test_revoking_a_leaf_leaves_ancestors_usable(self):
        self.authority.revoke("cap_leaf")
        self.assertFalse(self.authority.is_revoked(self.ancestor))
        self.assertFalse(self.authority.is_revoked(self.middle))
        self.assertTrue(self.authority.is_revoked(self.leaf))

    def test_unissued_revoked_parent_still_invalidates_child(self):
        # The receiving agent may only have the child token and a revocation list.
        authority = capability.CapabilityAuthority()
        authority.revoke(PARENT_ID)
        self.assertTrue(authority.is_revoked(token()))

    def test_revocation_is_audited(self):
        self.authority.revoke(PARENT_ID)
        targets = [entry["target"] for entry in self.authority.audit]
        self.assertEqual(targets, [PARENT_ID, "cap_middle", "cap_leaf"])


class ConsentRequirementTests(unittest.TestCase):
    def setUp(self):
        self.authority = capability.CapabilityAuthority()

    def test_l2_does_not_require_a_receipt(self):
        self.authority.require_consent(token(), risk="L2")

    def test_l3_requires_a_receipt(self):
        document = token()
        del document["consent_receipt_id"]
        with self.assertRaises(OsapError) as caught:
            self.authority.require_consent(document, risk="L3")
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_REQUIRED")

    def test_l4_requires_a_receipt(self):
        document = token()
        del document["consent_receipt_id"]
        with self.assertRaises(OsapError) as caught:
            self.authority.require_consent(document, risk="L4")
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_REQUIRED")

    def test_l3_with_a_receipt_is_accepted(self):
        self.authority.require_consent(token(), risk="L3")


if __name__ == "__main__":
    unittest.main()
