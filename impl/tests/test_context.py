# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for the context fabric (standard.md §9)."""

import json
import unittest
from datetime import timedelta
from pathlib import Path

from osap import OsapError, context
from osap.clock import parse_timestamp

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"

ORCHESTRATOR = "agent://com.example.orchestrator/main#1a2b"
NOTES = "agent://com.example.notes/assistant#7f3a"


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def handle(**overrides) -> dict:
    document = load("context-handle.json")
    document.update(overrides)
    return document


def now_of(document: dict):
    return parse_timestamp(document["created_at"])


def resolve(document: dict, **kwargs):
    fabric = context.ContextFabric()
    kwargs.setdefault("agent", document.get("audience"))
    kwargs.setdefault("granted_actions", ["resolve"])
    kwargs.setdefault("now", now_of(document))
    result = fabric.resolve(document, **kwargs)
    return fabric, result


class LabelTests(unittest.TestCase):
    def test_labels_are_ordered_from_public_to_secret(self):
        ranks = [context.label_rank(label) for label in context.LABELS]
        self.assertEqual(ranks, sorted(ranks))
        self.assertEqual(context.LABELS, ("public", "personal", "sensitive", "secret"))

    def test_unknown_label_is_schema_invalid(self):
        with self.assertRaises(OsapError) as caught:
            context.label_rank("top_secret")
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_stricter_label_picks_the_highest_rank(self):
        self.assertEqual(context.stricter_label("public", "sensitive", None), "sensitive")
        self.assertEqual(context.stricter_label("secret", "personal"), "secret")

    def test_stricter_label_of_nothing_is_none(self):
        self.assertIsNone(context.stricter_label(None, None))

    def test_lowered_label_is_reported(self):
        sources = {"obj://sha256:9f2c7b1a": "sensitive"}
        report = context.label_violation(handle(label="public"), sources)
        self.assertTrue(report["lowered"])
        self.assertFalse(report["conforming"])
        self.assertEqual(report["effective_label"], "sensitive")

    def test_raised_label_is_conforming(self):
        sources = {"obj://sha256:9f2c7b1a": "personal"}
        report = context.label_violation(handle(label="secret"), sources)
        self.assertFalse(report["lowered"])
        self.assertTrue(report["conforming"])
        self.assertEqual(report["effective_label"], "secret")

    def test_equal_label_is_conforming(self):
        sources = {"obj://sha256:9f2c7b1a": "personal"}
        report = context.label_violation(handle(label="personal"), sources)
        self.assertFalse(report["lowered"])
        self.assertEqual(report["effective_label"], "personal")

    def test_unknown_source_is_ignored(self):
        report = context.label_violation(handle(label="public"), {"obj://sha256:other": "secret"})
        self.assertFalse(report["lowered"])
        self.assertIsNone(report["inherited_label"])


class ExpiryTests(unittest.TestCase):
    def test_expires_at_wins_over_ttl(self):
        document = handle(expires_at="2026-11-10T10:20:00Z")
        self.assertEqual(context.expiry_of(document), parse_timestamp("2026-11-10T10:20:00Z"))

    def test_ttl_is_measured_from_created_at(self):
        document = handle(expires_at="", ttl=600)
        expected = parse_timestamp(document["created_at"]) + timedelta(seconds=600)
        self.assertEqual(context.expiry_of(document), expected)

    def test_no_expiry_returns_none(self):
        self.assertIsNone(context.expiry_of({"handle": "ctx://user/profile"}))


class ResolveTests(unittest.TestCase):
    def test_resolve_grant_is_accepted(self):
        document = handle()
        fabric, result = resolve(document)
        self.assertEqual(result["handle"], "ctx://user/profile#display_name")
        self.assertEqual(result["label"], "personal")
        self.assertEqual(fabric.audit[-1]["decision"], "allow")

    def test_read_grant_alone_is_not_enough(self):
        document = handle()
        with self.assertRaises(OsapError) as caught:
            resolve(document, granted_actions=["read"])
        self.assertEqual(caught.exception.code, "CONTEXT_DENIED")
        self.assertEqual(caught.exception.details["required_action"], "resolve")

    def test_denial_is_audited(self):
        document = handle()
        fabric = context.ContextFabric()
        with self.assertRaises(OsapError):
            fabric.resolve(
                document,
                agent=document["audience"],
                granted_actions=["read"],
                now=now_of(document),
            )
        self.assertEqual(fabric.audit[-1]["decision"], "deny")
        self.assertEqual(fabric.audit[-1]["action"], "context.resolve")
        self.assertEqual(fabric.audit[-1]["handle"], document["handle"])
        self.assertEqual(fabric.audit[-1]["agent"], document["audience"])

    def test_expired_handle_is_rejected(self):
        document = handle(expires_at="2026-11-10T09:00:00Z")
        with self.assertRaises(OsapError) as caught:
            resolve(document)
        self.assertEqual(caught.exception.code, "CONTEXT_EXPIRED")

    def test_expiry_is_not_renewed_by_resolving(self):
        document = handle()
        expired = now_of(document) + timedelta(seconds=600)
        with self.assertRaises(OsapError) as caught:
            resolve(document, now=expired)
        self.assertEqual(caught.exception.code, "CONTEXT_EXPIRED")
        self.assertNotIn("renewed", str(caught.exception.details))

    def test_audience_mismatch_is_denied(self):
        with self.assertRaises(OsapError) as caught:
            resolve(handle(), agent=NOTES)
        self.assertEqual(caught.exception.code, "CONTEXT_DENIED")
        self.assertEqual(caught.exception.details["reason"], "audience")

    def test_agent_outside_allowed_agents_is_denied(self):
        document = handle(constraints={"allowed_agents": [NOTES]})
        with self.assertRaises(OsapError) as caught:
            resolve(document)
        self.assertEqual(caught.exception.details["reason"], "agent_not_allowed")

    def test_allowed_agents_are_enforced_with_the_audience(self):
        document = handle(constraints={"allowed_agents": [ORCHESTRATOR]})
        result = resolve(document)[1]
        self.assertEqual(result["label"], "personal")

    def test_os_permission_denial_wins(self):
        document = handle()
        with self.assertRaises(OsapError) as caught:
            resolve(document, os_permission="denied")
        self.assertEqual(caught.exception.code, "CONTEXT_DENIED")
        self.assertEqual(caught.exception.details["reason"], "os_permission")

    def test_task_grant_does_not_read_long_term_memory(self):
        document = handle(handle="ctx://user/memory/preferences", scope="user")
        with self.assertRaises(OsapError) as caught:
            resolve(document, granted_actions=["task.read"])
        self.assertEqual(caught.exception.details["required_action"], context.MEMORY_ACTION)

    def test_memory_read_grant_resolves_a_memory_handle(self):
        document = handle(handle="ctx://user/memory/preferences", scope="user")
        result = resolve(document, granted_actions=["memory.read"])[1]
        self.assertEqual(result["scope"], "user")

    def test_user_scope_alone_is_not_memory(self):
        document = handle(scope="user")
        self.assertFalse(context.is_memory_handle(document))
        self.assertEqual(context.required_action(document), "resolve")


class EgressTests(unittest.TestCase):
    def test_secret_egress_without_approval_is_denied(self):
        with self.assertRaises(OsapError) as caught:
            resolve(handle(label="secret"), egress=True, user_approval=False)
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_REQUIRED")

    def test_sensitive_egress_without_approval_is_denied(self):
        with self.assertRaises(OsapError) as caught:
            resolve(handle(label="sensitive"), egress=True)
        self.assertEqual(caught.exception.code, "POLICY_CONSENT_REQUIRED")

    def test_secret_egress_with_approval_is_accepted(self):
        result = resolve(handle(label="secret"), egress=True, user_approval=True)[1]
        self.assertEqual(result["label"], "secret")

    def test_personal_egress_needs_no_approval(self):
        result = resolve(handle(), egress=True)[1]
        self.assertEqual(result["label"], "personal")


class BlackboardTests(unittest.TestCase):
    def test_task_end_archives_without_promotion(self):
        report = context.close_blackboard(load("blackboard.json"), task_ended=True)
        self.assertTrue(report["cleared_or_archived"])
        self.assertFalse(report["promoted_to_memory"])
        self.assertEqual(report["entries_archived"], 2)

    def test_running_task_keeps_the_count(self):
        report = context.close_blackboard(load("blackboard.json"), task_ended=False)
        self.assertFalse(report["task_ended"])
        self.assertTrue(report["cleared_or_archived"])


class DeleteTests(unittest.TestCase):
    def test_referenced_object_is_tombstoned_not_deleted(self):
        report = context.delete_object(
            "obj://sha256:9f2c7b1a", reference_count=2, hard_delete=False
        )
        self.assertFalse(report["deleted"])
        self.assertTrue(report["tombstoned"])
        self.assertTrue(report["references_checked"])
        self.assertTrue(report["audit_written"])
        self.assertTrue(report["conforming"])

    def test_hard_deleting_a_referenced_object_is_non_conforming(self):
        report = context.delete_object("obj://sha256:9f2c7b1a", reference_count=2, hard_delete=True)
        self.assertFalse(report["deleted"])
        self.assertFalse(report["conforming"])
        self.assertEqual(report["reference_count"], 2)

    def test_unreferenced_object_is_deleted(self):
        report = context.delete_object(
            "obj://sha256:9f2c7b1a", reference_count=0, hard_delete=False
        )
        self.assertTrue(report["deleted"])
        self.assertFalse(report["tombstoned"])
        self.assertTrue(report["conforming"])


class CacheTests(unittest.TestCase):
    def test_cache_ttl_is_clamped_to_the_handle_ttl(self):
        report = context.cache_window(handle(), requested_ttl=900, elapsed_seconds=700)
        self.assertTrue(report["clamped"])
        self.assertEqual(report["effective_ttl"], 600)
        self.assertFalse(report["cache_hit"])

    def test_entry_inside_the_window_is_a_hit(self):
        report = context.cache_window(handle(), requested_ttl=60, elapsed_seconds=30)
        self.assertFalse(report["clamped"])
        self.assertEqual(report["effective_ttl"], 60)
        self.assertTrue(report["cache_hit"])

    def test_handle_without_ttl_keeps_the_requested_ttl(self):
        report = context.cache_window(
            {"handle": "ctx://user/profile"}, requested_ttl=900, elapsed_seconds=0
        )
        self.assertFalse(report["clamped"])
        self.assertEqual(report["effective_ttl"], 900)


class StorageTests(unittest.TestCase):
    def test_managed_store_missing_duties_is_non_conforming(self):
        report = context.storage_declaration(
            "managed_store", {"quota": False, "garbage_collection": False}
        )
        self.assertFalse(report["conforming"])
        self.assertIn("quota", report["missing"])
        self.assertIn("garbage_collection", report["missing"])

    def test_complete_managed_store_is_conforming(self):
        declares = {duty: True for duty in context.STORAGE_DUTIES}
        report = context.storage_declaration("managed_store", declares)
        self.assertTrue(report["conforming"])
        self.assertEqual(report["missing"], [])

    def test_os_native_mode_owes_no_storage_duties(self):
        report = context.storage_declaration("os_native", {})
        self.assertFalse(report["declares_managed_store"])
        self.assertTrue(report["conforming"])


class MemoryTests(unittest.TestCase):
    def test_bus_state_is_not_memory(self):
        report = context.memory_promotions(["idempotency_index", "audit_log", "task_tree"])
        self.assertFalse(report["conforming"])
        self.assertEqual(
            report["promoted_to_memory"], ["idempotency_index", "audit_log", "task_tree"]
        )

    def test_blackboard_and_metadata_are_not_memory(self):
        report = context.memory_promotions(["blackboard", "object_metadata"])
        self.assertEqual(len(report["promoted_to_memory"]), 2)

    def test_explicit_memory_source_is_conforming(self):
        report = context.memory_promotions(["memory_entries", "contacts"])
        self.assertTrue(report["conforming"])
        self.assertEqual(report["promoted_to_memory"], [])


if __name__ == "__main__":
    unittest.main()
