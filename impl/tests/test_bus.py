# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for the Bus core (standard.md §7.1, §7.7, §7.8)."""

import json
import unittest
from pathlib import Path

from osap import Bus, OsapError, envelope
from osap.clock import Deadline
from osap.clock import parse_timestamp

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


class HandshakeTests(unittest.TestCase):
    def test_request_before_hello_is_rejected(self):
        with self.assertRaises(OsapError) as caught:
            Bus().receive(load("request.json"))
        self.assertEqual(caught.exception.code, "TRANSPORT_HANDSHAKE_REQUIRED")

    def test_incompatible_version_is_rejected(self):
        with self.assertRaises(OsapError) as caught:
            Bus().handshake({"osap": "1.0"})
        self.assertEqual(caught.exception.code, "TRANSPORT_VERSION_UNSUPPORTED")

    def test_welcome_is_a_valid_envelope(self):
        bus = Bus()
        welcome = bus.handshake(load("hello.json"))
        envelope.validate(welcome)
        self.assertEqual(bus.state, "ready")
        self.assertEqual(welcome["body"]["data"]["binding"], "stream")

    def test_hello_completes_the_handshake(self):
        bus = Bus()
        welcome = bus.receive(load("hello.json"))
        self.assertEqual(welcome["type"], "welcome")
        self.assertEqual(bus.state, "ready")


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.bus = Bus()
        self.bus.handshake({"osap": "0.1"})

    def test_unknown_type_is_schema_unsupported(self):
        message = load("request.json")
        message["type"] = "bogus"
        with self.assertRaises(OsapError) as caught:
            self.bus.receive(message)
        self.assertEqual(caught.exception.code, "SCHEMA_UNSUPPORTED")

    def test_duplicate_id_runs_side_effects_once(self):
        message = load("request.json")
        first = self.bus.receive(message)
        second = self.bus.receive(message)
        self.assertFalse(first["replayed"])
        self.assertTrue(second["replayed"])
        self.assertEqual(self.bus.side_effects, 1)
        self.assertEqual(self.bus.replays, 1)

    def test_unrouted_type_raises_not_implemented(self):
        message = load("request.json")
        message["type"] = "discover"
        with self.assertRaises(NotImplementedError):
            self.bus.receive(message)

    def test_error_envelope_is_valid(self):
        message = load("request.json")
        reply = self.bus.error_envelope(message, OsapError("POLICY_DENIED", "denied"))
        envelope.validate(reply)
        self.assertEqual(reply["body"]["data"]["code"], "POLICY_DENIED")
        self.assertEqual(reply["causation_id"], message["id"])


class ClockTests(unittest.TestCase):
    def test_wall_rollback_does_not_revive_a_deadline(self):
        now = [0.0]
        deadline = Deadline(15.0, monotonic=lambda: now[0])
        now[0] = 16.0
        with self.assertRaises(OsapError) as caught:
            deadline.check()
        self.assertEqual(caught.exception.code, "TIMEOUT")

    def test_deadline_from_envelope(self):
        message = load("request.json")
        deadline = Deadline.from_envelope(message)
        self.assertAlmostEqual(deadline.budget, 15.0)
        self.assertFalse(deadline.expired())

    def test_timestamp_requires_timezone_aware_input(self):
        self.assertEqual(parse_timestamp("2026-11-10T10:14:45Z").utcoffset().total_seconds(), 0)


if __name__ == "__main__":
    unittest.main()
