# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for envelope validation (standard.md §7.1, §7.9)."""

import copy
import json
import unittest
from pathlib import Path

from osap import OsapError, envelope, errors

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def request() -> dict:
    return json.loads((EXAMPLES / "request.json").read_text(encoding="utf-8"))


class EnvelopeTests(unittest.TestCase):
    def test_example_request_is_valid(self):
        self.assertEqual(envelope.validate(request())["type"], "request")

    def test_unknown_type_is_schema_unsupported(self):
        message = request()
        message["type"] = "bogus"
        with self.assertRaises(OsapError) as caught:
            envelope.validate(message)
        self.assertEqual(caught.exception.code, "SCHEMA_UNSUPPORTED")

    def test_incompatible_major_is_rejected(self):
        message = request()
        message["osap"] = "1.0"
        with self.assertRaises(OsapError) as caught:
            envelope.validate(message)
        self.assertEqual(caught.exception.code, "TRANSPORT_VERSION_UNSUPPORTED")

    def test_missing_version_is_schema_invalid(self):
        message = request()
        del message["osap"]
        with self.assertRaises(OsapError) as caught:
            envelope.validate(message)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_missing_auth_is_schema_invalid(self):
        message = request()
        del message["auth"]
        with self.assertRaises(OsapError) as caught:
            envelope.validate(message)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")
        self.assertIn("auth", caught.exception.message)

    def test_second_route_key_is_schema_invalid(self):
        message = copy.deepcopy(request())
        message["to"]["agent"] = "agent://com.example.notes/assistant#7f3a"
        with self.assertRaises(OsapError) as caught:
            envelope.validate(message)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")

    def test_route_kind(self):
        self.assertEqual(envelope.route_kind(request()), "capability")

    def test_task_id(self):
        self.assertEqual(envelope.task_id(request()), "task_01J9Z6Q3V8N2K4M7P1R5T0WXAB")


class ErrorModelTests(unittest.TestCase):
    def test_standard_code_is_marked(self):
        error = OsapError("POLICY_DENIED")
        self.assertTrue(error.standard)
        self.assertFalse(error.retryable)

    def test_retryable_defaults_from_the_table(self):
        self.assertTrue(OsapError("RATE_LIMIT").retryable)
        self.assertFalse(OsapError("AUTH_DENIED").retryable)

    def test_extension_code_is_recognised(self):
        error = OsapError("AUDIT_CHAIN_INVALID")
        self.assertFalse(error.standard)
        self.assertFalse(errors.is_extension("AUDIT_CHAIN_INVALID"))
        self.assertTrue(errors.is_extension("POLICY_VENDOR_DENIED"))

    def test_error_body_shape(self):
        data = OsapError("TIMEOUT", "late", details={"k": 1}).to_data()
        self.assertEqual(data["code"], "TIMEOUT")
        self.assertTrue(data["retryable"])
        self.assertEqual(data["details"], {"k": 1})


if __name__ == "__main__":
    unittest.main()
