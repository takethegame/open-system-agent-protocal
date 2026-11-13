# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for registration (standard.md §4.1–§4.7)."""

import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from osap import OsapError, crypto, identity, registry

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
AGENT = "agent://com.example.notes/assistant#7f3a"
APP = "app://com.example.notes"
PUBLIC_KEY = "base64url-example-public-key"


def hello() -> dict:
    return json.loads((EXAMPLES / "hello.json").read_text(encoding="utf-8"))


def signed_manifest() -> tuple[dict, str]:
    private, public = crypto.generate_keypair()
    manifest = {
        "osap_manifest": "0.1",
        "app": APP,
        "version": "1.0.0",
        "signature": "",
        "agents": [
            {
                "agent": AGENT,
                "display_name": "Notes Assistant",
                "public_key": PUBLIC_KEY,
                "capabilities": [
                    {
                        "cap": "cap://os/notes/documents",
                        "actions": ["read", "write"],
                        "resources": ["notes:local"],
                        "schemas": ["osap.notes.document/v1"],
                        "risk": "L2",
                        "consent": "first_use",
                    }
                ],
            }
        ],
    }
    return crypto.sign_document(manifest, private), public


def registered_registry() -> registry.Registry:
    manifest, public = signed_manifest()
    instance = registry.Registry()
    instance.trust(APP, public)
    instance.index_manifest(manifest)
    return instance


class RegistrationTests(unittest.TestCase):
    def test_valid_hello_returns_welcome(self):
        welcome = identity.Registrar(registered_registry()).register(hello())
        self.assertEqual(welcome["type"], "welcome")
        self.assertTrue(welcome["session_id"].startswith("session_"))
        self.assertEqual(welcome["body"]["data"]["app"], APP)

    def test_sender_must_match_claimed_agent(self):
        message = hello()
        message["from"] = "agent://com.example.notes/assistant#0000"
        with self.assertRaises(OsapError) as caught:
            identity.Registrar(registered_registry()).register(message)
        self.assertEqual(caught.exception.code, "AUTH_DENIED")

    def test_reserved_namespace_is_denied(self):
        message = hello()
        message["from"] = "agent://system/registry#0"
        message["body"]["data"]["agent"] = "agent://system/registry#0"
        with self.assertRaises(OsapError) as caught:
            identity.Registrar(registered_registry()).register(message)
        self.assertEqual(caught.exception.code, "AUTH_DENIED")

    def test_agent_cannot_claim_another_app(self):
        message = hello()
        message["body"]["data"]["app"] = "app://com.example.calendar"
        with self.assertRaises(OsapError) as caught:
            identity.Registrar(registered_registry()).register(message)
        self.assertEqual(caught.exception.code, "AUTH_DENIED")

    def test_unregistered_app_is_denied(self):
        with self.assertRaises(OsapError) as caught:
            identity.Registrar(registry.Registry()).register(hello())
        self.assertEqual(caught.exception.code, "AUTH_DENIED")

    def test_unbound_public_key_is_denied(self):
        message = hello()
        message["body"]["data"]["public_key"] = "base64url-unbound-public-key"
        with self.assertRaises(OsapError) as caught:
            identity.Registrar(registered_registry()).register(message)
        self.assertEqual(caught.exception.code, "AUTH_DENIED")

    def test_manifest_signature_is_verified(self):
        instance = registered_registry()
        manifest = copy.deepcopy(instance.manifest_for(APP))
        manifest["signature"] = "base64url-invalid-signature"
        with self.assertRaises(OsapError) as caught:
            instance.index_manifest(manifest)
        self.assertEqual(caught.exception.code, "AUTH_DENIED")

    def test_rotated_key_outside_grace_is_denied(self):
        instance = registered_registry()
        instance.mark_rotated(
            AGENT, rotated_at=datetime.now(timezone.utc) - timedelta(hours=1), grace_seconds=0
        )
        with self.assertRaises(OsapError) as caught:
            identity.Registrar(instance).register(hello())
        self.assertEqual(caught.exception.code, "AUTH_DENIED")

    def test_rotated_key_inside_grace_is_accepted(self):
        instance = registered_registry()
        instance.mark_rotated(
            AGENT, rotated_at=datetime.now(timezone.utc) - timedelta(minutes=1), grace_seconds=3600
        )
        welcome = identity.Registrar(instance).register(hello())
        self.assertEqual(welcome["type"], "welcome")

    def test_app_of_agent(self):
        self.assertEqual(identity.app_of_agent(AGENT), APP)

    def test_reserved_prefixes(self):
        for name in ("agent://system/bus#0", "cap://os/calendar/events", "ctx://os/x"):
            self.assertTrue(identity.is_reserved(name))
        self.assertFalse(identity.is_reserved(AGENT))


if __name__ == "__main__":
    unittest.main()
