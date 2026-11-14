# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for the federation adapters (standard.md §6.7, §6.8)."""

import copy
import json
import unittest
from pathlib import Path

from osap import OsapError, federation

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def record(**source) -> dict:
    document = load("capability-record.json")
    document["source"] = {
        "kind": "mcp",
        "registry": "mcp",
        "native_id": "calendar-server:create_event",
        **source,
    }
    return document


def with_trust(level: str, kind: str = "mcp", native_id: str = "server:tool") -> dict:
    document = record(kind=kind, native_id=native_id)
    document["provenance"]["trust"] = level
    return document


class ProjectionTests(unittest.TestCase):
    def test_vendor_record_keeps_its_native_identity(self):
        projection = federation.project(load("capability-record.json"))
        self.assertEqual(projection["source_kind"], "vendor_registry")
        self.assertEqual(projection["registry"], "android.appfunctions")
        self.assertEqual(projection["native_id"], "com.example.calendar.createEvent")
        self.assertEqual(projection["trust"], "system")
        self.assertEqual(projection["origin"], "local")

    def test_schema_is_the_first_declared_schema(self):
        projection = federation.project(load("capability-record.json"))
        self.assertEqual(projection["schema"], "osap.calendar.event/v1")

    def test_projection_keeps_the_source_version(self):
        projection = federation.project(load("capability-record.json"))
        self.assertEqual(projection["version"], "1.0.0")

    def test_projection_does_not_mutate_the_record(self):
        document = record()
        before = copy.deepcopy(document)
        federation.project(document)
        self.assertEqual(document, before)

    def test_missing_freshness_is_schema_invalid(self):
        document = record()
        del document["freshness"]
        with self.assertRaises(OsapError) as caught:
            federation.project(document)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_unknown_source_kind_is_schema_invalid(self):
        document = record(kind="telepathy")
        with self.assertRaises(OsapError) as caught:
            federation.project(document)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")


class NativeIdTests(unittest.TestCase):
    def test_mcp_identity_is_server_and_tool(self):
        self.assertEqual(
            federation.parse_native_id("mcp", "calendar-server:create_event"),
            {"server": "calendar-server", "tool": "create_event"},
        )

    def test_mcp_identity_needs_both_parts(self):
        with self.assertRaises(OsapError) as caught:
            federation.parse_native_id("mcp", "calendar-server")
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_a2a_identity_is_card_and_skill(self):
        native = "https://calendar.example/.well-known/agent.json#create_event"
        self.assertEqual(
            federation.parse_native_id("a2a", native),
            {
                "agent_card": "https://calendar.example/.well-known/agent.json",
                "skill": "create_event",
            },
        )

    def test_a2a_identity_needs_a_skill_fragment(self):
        with self.assertRaises(OsapError):
            federation.parse_native_id("a2a", "https://calendar.example/agent.json")

    def test_dbus_identity_splits_bus_path_interface_and_method(self):
        native = (
            "session:org.example.Calendar:/org/example/Calendar:"
            "org.example.Calendar.CreateEvent"
        )
        self.assertEqual(
            federation.parse_native_id("dbus", native),
            {
                "bus": "session",
                "path": "/org/example/Calendar",
                "interface": "org.example.Calendar",
                "method": "CreateEvent",
            },
        )

    def test_dbus_identity_needs_four_segments(self):
        with self.assertRaises(OsapError):
            federation.parse_native_id("dbus", "session:org.example.Calendar")

    def test_openapi_identity_is_the_operation(self):
        self.assertEqual(
            federation.parse_native_id("openapi", "createEvent"),
            {"operation": "createEvent"},
        )

    def test_vendor_identity_has_no_extra_fields(self):
        self.assertEqual(federation.parse_native_id("vendor_registry", "com.example.run"), {})


class TrustTests(unittest.TestCase):
    def test_external_source_keeps_origin_external(self):
        self.assertEqual(federation.project(record())["origin"], "external")

    def test_external_system_claim_is_capped_to_unverified(self):
        projection = federation.project(with_trust("system"))
        self.assertEqual(projection["trust"], "unverified")
        self.assertEqual(projection["origin"], "external")

    def test_external_verified_claim_is_also_unverified(self):
        self.assertEqual(federation.project(with_trust("verified"))["trust"], "unverified")

    def test_a2a_and_openapi_are_external(self):
        for kind, native in (("a2a", "card#skill"), ("openapi", "createEvent")):
            projection = federation.project(with_trust("system", kind=kind, native_id=native))
            self.assertEqual(projection["origin"], "external")
            self.assertEqual(projection["trust"], "unverified")

    def test_vendor_registry_keeps_system_trust(self):
        document = load("capability-record.json")
        self.assertEqual(federation.project(document)["trust"], "system")

    def test_dbus_is_local(self):
        native = (
            "session:org.example.Calendar:/org/example/Calendar:"
            "org.example.Calendar.CreateEvent"
        )
        projection = federation.project(with_trust("system", "dbus", native))
        self.assertEqual(projection["origin"], "local")
        self.assertEqual(projection["trust"], "system")

    def test_unknown_trust_is_rejected(self):
        with self.assertRaises(OsapError) as caught:
            federation.effective_trust("native", "trusted")
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")


class NamespaceTests(unittest.TestCase):
    def test_mapped_capability_is_deterministic(self):
        source = record()["source"]
        first = federation.mapped_capability(source)
        second = federation.mapped_capability(dict(source))
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("cap://federation/mcp/"))

    def test_registry_participates_in_the_name(self):
        one = federation.mapped_capability(
            {"registry": "mcp", "native_id": "calendar-server:create_event"}
        )
        two = federation.mapped_capability(
            {"registry": "a2a", "native_id": "calendar-server:create_event"}
        )
        self.assertNotEqual(one, two)

    def test_native_separators_are_escaped(self):
        mapped = federation.mapped_capability(
            {"registry": "android.appfunctions", "native_id": "com.example.calendar.createEvent"}
        )
        expected = "cap://federation/android-appfunctions/com.example.calendar.createEvent"
        self.assertEqual(mapped, expected)


class RefreshTests(unittest.TestCase):
    def test_refresh_moves_the_window(self):
        document = load("capability-record.json")
        refreshed = federation.refresh(
            document,
            observed_at="2026-11-11T10:00:00Z",
            expires_at="2026-11-12T10:00:00Z",
        )
        self.assertEqual(refreshed["freshness"]["expires_at"], "2026-11-12T10:00:00Z")
        self.assertEqual(document["freshness"]["expires_at"], "2026-11-11T10:00:00Z")

    def test_refreshed_record_still_projects(self):
        document = load("capability-record.json")
        refreshed = federation.refresh(
            document,
            observed_at="2026-11-11T10:00:00Z",
            expires_at="2026-11-12T10:00:00Z",
        )
        self.assertEqual(federation.project(refreshed)["record_id"], document["record_id"])


if __name__ == "__main__":
    unittest.main()
