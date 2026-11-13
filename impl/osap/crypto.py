# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Ed25519 signatures for manifests and records (standard.md §4.5, §6.1).

Signatures cover the canonical JSON of the document with the `signature`
field removed. Canonical form is key-sorted, separator-minimal UTF-8 JSON.
This is not RFC 8785 in full, but it is deterministic for the documents OSAP
signs and is written down so other implementations can reproduce it.
"""

from __future__ import annotations

import base64
import binascii
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from .errors import OsapError

SIGNATURE_FIELD = "signature"


def b64encode(data: bytes) -> str:
    """Base64url without padding (RFC 4648 §5)."""

    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64decode(text: str) -> bytes:
    """Decode base64url, accepting missing padding."""

    padded = text + "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def canonical_bytes(document: dict, *, drop: tuple[str, ...] = (SIGNATURE_FIELD,)) -> bytes:
    """Return deterministic UTF-8 JSON for signing or verification."""

    body = {key: value for key, value in document.items() if key not in drop}
    return json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def generate_keypair() -> tuple[str, str]:
    """Return `(private_b64, public_b64)` for a fresh Ed25519 key."""

    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    private_raw = private.private_bytes_raw()
    return b64encode(private_raw), b64encode(public)


def public_from_private(private_b64: str) -> str:
    private = Ed25519PrivateKey.from_private_bytes(b64decode(private_b64))
    return b64encode(private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))


def sign_bytes(payload: bytes, private_b64: str) -> str:
    private = Ed25519PrivateKey.from_private_bytes(b64decode(private_b64))
    return b64encode(private.sign(payload))


def verify_bytes(payload: bytes, signature_b64: str, public_b64: str) -> bool:
    """Verify a signature; malformed input counts as a failed verification."""

    try:
        public = Ed25519PublicKey.from_public_bytes(b64decode(public_b64))
        public.verify(b64decode(signature_b64), payload)
    except (InvalidSignature, ValueError, TypeError, binascii.Error):
        return False
    return True


def sign_document(document: dict, private_b64: str) -> dict:
    """Return a copy of `document` with a fresh `signature`."""

    signed = {key: value for key, value in document.items() if key != SIGNATURE_FIELD}
    signed[SIGNATURE_FIELD] = sign_bytes(canonical_bytes(document), private_b64)
    return signed


def verify_document(document: dict, public_b64: str) -> bool:
    """Verify the `signature` field of a document against `public_b64`."""

    signature = document.get(SIGNATURE_FIELD)
    if not isinstance(signature, str) or not signature:
        return False
    return verify_bytes(canonical_bytes(document), signature, public_b64)


def require_verified(document: dict, public_b64: str | None, *, what: str) -> None:
    """Raise `AUTH_DENIED` unless the document signature verifies."""

    if public_b64 is None:
        raise OsapError("AUTH_DENIED", f"{what} is signed by an unknown app")
    if not verify_document(document, public_b64):
        raise OsapError("AUTH_DENIED", f"{what} signature does not verify")
