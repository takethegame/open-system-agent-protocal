# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for manifest signing (standard.md §4.5, §6.1)."""

import copy
import unittest

from osap import OsapError, crypto


def manifest() -> dict:
    return {
        "osap_manifest": "0.1",
        "app": "app://com.example.notes",
        "version": "1.0.0",
        "signature": "",
        "agents": [
            {
                "agent": "agent://com.example.notes/assistant#7f3a",
                "display_name": "Notes Assistant",
                "public_key": "base64url-example-public-key",
                "capabilities": [
                    {
                        "cap": "cap://os/notes/documents",
                        "actions": ["read"],
                        "resources": ["notes:local"],
                        "schemas": ["osap.notes.document/v1"],
                        "risk": "L1",
                    }
                ],
            }
        ],
    }


class SignatureTests(unittest.TestCase):
    def setUp(self):
        self.private, self.public = crypto.generate_keypair()

    def test_public_key_matches_private_key(self):
        self.assertEqual(crypto.public_from_private(self.private), self.public)

    def test_sign_then_verify(self):
        signed = crypto.sign_document(manifest(), self.private)
        self.assertTrue(crypto.verify_document(signed, self.public))

    def test_canonical_form_ignores_key_order(self):
        signed = crypto.sign_document(manifest(), self.private)
        reordered = dict(reversed(list(manifest().items())))
        reordered["signature"] = signed["signature"]
        self.assertTrue(crypto.verify_document(reordered, self.public))

    def test_tampered_document_fails(self):
        signed = crypto.sign_document(manifest(), self.private)
        tampered = copy.deepcopy(signed)
        tampered["version"] = "2.0.0"
        self.assertFalse(crypto.verify_document(tampered, self.public))

    def test_tampered_signature_fails(self):
        signed = crypto.sign_document(manifest(), self.private)
        tampered = dict(signed)
        tampered["signature"] = "base64url-invalid-signature"
        self.assertFalse(crypto.verify_document(tampered, self.public))

    def test_wrong_key_fails(self):
        _other_private, other_public = crypto.generate_keypair()
        signed = crypto.sign_document(manifest(), self.private)
        self.assertFalse(crypto.verify_document(signed, other_public))

    def test_missing_signature_fails(self):
        unsigned = manifest()
        del unsigned["signature"]
        self.assertFalse(crypto.verify_document(unsigned, self.public))

    def test_require_verified_raises_auth_denied(self):
        with self.assertRaises(OsapError) as caught:
            crypto.require_verified(manifest(), None, what="app manifest")
        self.assertEqual(caught.exception.code, "AUTH_DENIED")


if __name__ == "__main__":
    unittest.main()
