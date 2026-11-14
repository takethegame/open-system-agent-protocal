# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for the task model (standard.md §8)."""

import copy
import json
import unittest
from pathlib import Path

from osap import OsapError, task

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"

ORCHESTRATOR = "agent://com.example.orchestrator/main#1a2b"
CALENDAR = "agent://com.example.calendar/agent#9c"


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def parent_task() -> task.Task:
    return task.Task.from_document(load("task.json"))


def child_record(
    task_id: str = "task_child",
    parent: str = "task_01J9Z6Q3V8N2K4M7P1R5T0WXAB",
    **overrides,
) -> task.Task:
    record = {
        "task_id": task_id,
        "parent_task_id": parent,
        "root_task_id": "task_01J9Z6Q3V8N2K4M7P1R5T0WXAA",
        "mode": "supervisor",
        "owner": ORCHESTRATOR,
        "assignee": CALENDAR,
        "budget": {"wall_ms": 1000},
        "status": "running",
    }
    record.update(overrides)
    return task.Task.from_document(record)


class BudgetTests(unittest.TestCase):
    def test_within_budget_is_accepted(self):
        task.check_budget({"wall_ms": 5000, "tool_calls": 2}, {"wall_ms": 5000, "tool_calls": 2})

    def test_wall_ms_overflow_is_rejected(self):
        with self.assertRaises(OsapError) as caught:
            task.check_budget({"wall_ms": 5000}, {"wall_ms": 6000})
        self.assertEqual(caught.exception.code, "TASK_BUDGET_EXCEEDED")
        self.assertEqual(caught.exception.details["dimension"], "wall_ms")

    def test_tool_call_overflow_is_rejected(self):
        with self.assertRaises(OsapError) as caught:
            task.check_budget({"tool_calls": 2}, {"tool_calls": 3})
        self.assertEqual(caught.exception.details["dimension"], "tool_calls")

    def test_unbounded_dimension_is_not_checked(self):
        task.check_budget({"wall_ms": 5000}, {"tokens": 10_000})

    def test_money_overflow_is_rejected(self):
        budget = {"money": {"currency": "USD", "amount": 1}}
        with self.assertRaises(OsapError) as caught:
            task.check_budget(budget, {"money": {"currency": "USD", "amount": 2}})
        self.assertEqual(caught.exception.details["dimension"], "money")

    def test_money_currency_mismatch_is_rejected(self):
        budget = {"money": {"currency": "USD", "amount": 1}}
        with self.assertRaises(OsapError):
            task.check_budget(budget, {"money": {"currency": "EUR", "amount": 1}})

    def test_remaining_budget_never_goes_negative(self):
        left = task.remaining_budget({"wall_ms": 1000, "tool_calls": 2}, {"wall_ms": 1500})
        self.assertEqual(left["wall_ms"], 0)
        self.assertEqual(left["tool_calls"], 2)


class TaskDocumentTests(unittest.TestCase):
    def test_example_task_is_valid(self):
        record = parent_task()
        self.assertEqual(record.owner, ORCHESTRATOR)
        self.assertEqual(record.result_schema, "osap.calendar.proposal/v1")

    def test_missing_budget_is_schema_invalid(self):
        document = load("task.json")
        del document["budget"]
        with self.assertRaises(OsapError) as caught:
            task.Task.from_document(document)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_snapshot_is_independent(self):
        record = parent_task()
        snapshot = record.snapshot()
        snapshot["budget"]["wall_ms"] = 1
        self.assertEqual(record.budget["wall_ms"], 8000)


class StateMachineTests(unittest.TestCase):
    def setUp(self):
        self.board = task.TaskBoard()
        self.record = self.board.add(parent_task())

    def test_created_to_accepted_to_running(self):
        self.board.transition(self.record, "accepted")
        self.board.transition(self.record, "running")
        self.assertEqual(self.record.status, "running")

    def test_created_to_succeeded_is_illegal(self):
        with self.assertRaises(OsapError) as caught:
            self.board.transition(self.record, "succeeded")
        self.assertEqual(caught.exception.code, "POLICY_DENIED")

    def test_unknown_status_is_schema_invalid(self):
        with self.assertRaises(OsapError) as caught:
            self.board.transition(self.record, "sleeping")
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_transitions_are_audited(self):
        self.board.transition(self.record, "accepted")
        self.assertEqual(self.board.audit[-1]["action"], "task.status")


class CancellationTests(unittest.TestCase):
    def setUp(self):
        self.board = task.TaskBoard()
        self.root = self.board.add(parent_task())
        self.child = self.board.add(child_record("task_child", parent=self.root.task_id))
        self.grandchild = self.board.add(child_record("task_grandchild", parent="task_child"))

    def test_cancel_propagates_to_descendants(self):
        cancelled = self.board.cancel(self.root.task_id)
        self.assertEqual(cancelled, [self.root.task_id, "task_child", "task_grandchild"])
        self.assertEqual(self.grandchild.status, "cancelled")

    def test_detached_child_keeps_running(self):
        self.child.detached = True
        cancelled = self.board.cancel(self.root.task_id)
        self.assertEqual(cancelled, [self.root.task_id])
        self.assertEqual(self.child.status, "running")

    def test_terminal_tasks_are_not_cancelled_again(self):
        self.child.status = "succeeded"
        cancelled = self.board.cancel(self.root.task_id)
        self.assertNotIn("task_child", cancelled)
        self.assertEqual(self.child.status, "succeeded")

    def test_unknown_task_is_routing_not_found(self):
        with self.assertRaises(OsapError) as caught:
            self.board.cancel("task_missing")
        self.assertEqual(caught.exception.code, "ROUTING_NOT_FOUND")


class DelegationTests(unittest.TestCase):
    def setUp(self):
        self.board = task.TaskBoard()
        self.parent = self.board.add(parent_task())
        self.message = load("delegate.json")

    def test_valid_delegation_creates_a_child(self):
        child = self.board.delegate(self.parent.task_id, self.message)
        self.assertEqual(child.task_id, "task_01J9Z6Q3V8N2K4M7P1R5T0WXAE")
        self.assertEqual(child.parent_task_id, self.parent.task_id)
        self.assertEqual(child.authority["cap_id"], "cap_01J9Z6Q3V8N2K4M7P1R5T0WXAD")

    def test_budget_above_the_parent_remainder_is_rejected(self):
        message = copy.deepcopy(self.message)
        message["body"]["data"]["budget"]["wall_ms"] = 9000
        with self.assertRaises(OsapError) as caught:
            self.board.delegate(self.parent.task_id, message)
        self.assertEqual(caught.exception.code, "POLICY_DENIED")
        self.assertEqual(caught.exception.details["dimension"], "wall_ms")

    def test_budget_equal_to_the_remainder_is_accepted(self):
        message = copy.deepcopy(self.message)
        message["body"]["data"]["budget"]["wall_ms"] = 8000
        self.board.delegate(self.parent.task_id, message)

    def test_depth_must_be_parent_plus_one(self):
        message = copy.deepcopy(self.message)
        message["body"]["data"]["budget"]["depth"] = 3
        with self.assertRaises(OsapError) as caught:
            self.board.delegate(self.parent.task_id, message)
        self.assertEqual(caught.exception.code, "POLICY_DENIED")
        self.assertIn("depth", caught.exception.message)

    def test_parent_mismatch_is_rejected(self):
        message = copy.deepcopy(self.message)
        message["task"]["parent"] = "task_other"
        with self.assertRaises(OsapError) as caught:
            self.board.delegate(self.parent.task_id, message)
        self.assertEqual(caught.exception.code, "POLICY_DENIED")

    def test_duplicate_child_is_rejected(self):
        self.board.delegate(self.parent.task_id, self.message)
        with self.assertRaises(OsapError) as caught:
            self.board.delegate(self.parent.task_id, self.message)
        self.assertEqual(caught.exception.code, "DUPLICATE")

    def test_delegation_is_audited(self):
        child = self.board.delegate(self.parent.task_id, self.message)
        self.assertEqual(self.board.audit[-1]["action"], "task.delegated")
        self.assertEqual(self.board.audit[-1]["task_id"], child.task_id)


class ResultTests(unittest.TestCase):
    def setUp(self):
        self.board = task.TaskBoard()
        self.record = self.board.add(parent_task())
        self.board.transition(self.record, "accepted")
        self.board.transition(self.record, "running")
        self.message = load("result.json")

    def test_matching_result_is_accepted(self):
        self.board.accept_result(self.message)
        self.assertEqual(self.record.status, "succeeded")

    def test_schema_mismatch_is_rejected(self):
        message = copy.deepcopy(self.message)
        message["body"]["schema"] = "osap.calendar.propose/v1"
        with self.assertRaises(OsapError) as caught:
            self.board.accept_result(message)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_non_assignee_result_is_rejected(self):
        message = copy.deepcopy(self.message)
        message["from"] = "agent://com.example.notes/agent#77"
        with self.assertRaises(OsapError) as caught:
            self.board.accept_result(message)
        self.assertEqual(caught.exception.code, "POLICY_DENIED")


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.board = task.TaskBoard()
        self.record = self.board.add(parent_task())
        self.message = load("handoff.json")

    def test_accepted_handoff_transfers_ownership(self):
        result = self.board.handoff(self.record, self.message)
        self.assertEqual(result, "accepted")
        self.assertEqual(self.record.owner, CALENDAR)
        self.assertEqual(self.record.assignee, CALENDAR)
        self.assertEqual(self.record.authority["cap_id"], "cap_01J9Z6Q3V8N2K4M7P1R5T0WXAF")

    def test_rejected_handoff_changes_nothing(self):
        before = self.record.snapshot()
        result = self.board.handoff(self.record, self.message, accepted=False)
        self.assertEqual(result, "rejected")
        self.assertEqual(self.record.snapshot(), before)

    def test_non_owner_cannot_hand_off(self):
        message = copy.deepcopy(self.message)
        message["from"] = CALENDAR
        with self.assertRaises(OsapError) as caught:
            self.board.handoff(self.record, message)
        self.assertEqual(caught.exception.code, "POLICY_DENIED")

    def test_l3_handoff_needs_a_fresh_receipt(self):
        with self.assertRaises(OsapError) as caught:
            self.board.handoff(self.record, self.message, risk="L3", renewed_consent=True)
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_REQUIRED")

    def test_l3_handoff_with_receipt_and_renewal_is_accepted(self):
        message = copy.deepcopy(self.message)
        message["body"]["data"]["delegated_capability"]["consent_receipt_id"] = "consent_1"
        self.assertEqual(
            self.board.handoff(self.record, message, risk="L3", renewed_consent=True),
            "accepted",
        )

    def test_l3_handoff_with_receipt_but_no_renewal_is_rejected(self):
        message = copy.deepcopy(self.message)
        message["body"]["data"]["delegated_capability"]["consent_receipt_id"] = "consent_1"
        with self.assertRaises(OsapError) as caught:
            self.board.handoff(self.record, message, risk="L3", renewed_consent=False)
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_REQUIRED")

    def test_audience_must_match_the_new_owner(self):
        message = copy.deepcopy(self.message)
        capability = message["body"]["data"]["delegated_capability"]
        capability["audience"] = "agent://com.example.notes/a#1"
        with self.assertRaises(OsapError) as caught:
            self.board.handoff(self.record, message)
        self.assertEqual(caught.exception.code, "CAPABILITY_AUDIENCE_MISMATCH")

    def test_subject_must_match_the_new_owner(self):
        message = copy.deepcopy(self.message)
        capability = message["body"]["data"]["delegated_capability"]
        capability["subject"] = "agent://com.example.notes/a#1"
        with self.assertRaises(OsapError) as caught:
            self.board.handoff(self.record, message)
        self.assertEqual(caught.exception.code, "CAPABILITY_SUBJECT_MISMATCH")

    def test_capability_must_be_bound_to_the_task(self):
        message = copy.deepcopy(self.message)
        message["body"]["data"]["delegated_capability"]["task_id"] = "task_other"
        with self.assertRaises(OsapError) as caught:
            self.board.handoff(self.record, message)
        self.assertEqual(caught.exception.code, "CAPABILITY_TASK_MISMATCH")

    def test_handoff_is_audited(self):
        self.board.handoff(self.record, self.message)
        entry = self.board.audit[-1]
        self.assertEqual(entry["action"], "task.handoff")
        self.assertEqual(entry["to"], CALENDAR)


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.board = task.TaskBoard()
        self.record = self.board.add(parent_task())

    def test_owner_may_keep_sending(self):
        self.board.require_owner(self.record.task_id, ORCHESTRATOR)

    def test_former_owner_is_refused_after_handoff(self):
        self.board.handoff(self.record, load("handoff.json"))
        with self.assertRaises(OsapError) as caught:
            self.board.require_owner(self.record.task_id, ORCHESTRATOR)
        self.assertEqual(caught.exception.code, "POLICY_DENIED")

    def test_new_owner_may_send(self):
        self.board.handoff(self.record, load("handoff.json"))
        self.board.require_owner(self.record.task_id, CALENDAR)

    def test_unknown_task_is_routing_not_found(self):
        with self.assertRaises(OsapError) as caught:
            self.board.require_owner("task_missing", ORCHESTRATOR)
        self.assertEqual(caught.exception.code, "ROUTING_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
