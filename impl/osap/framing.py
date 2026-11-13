# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Framing rules from standard.md §7.9.

- stream bindings (UDS, named pipe, localhost mTLS) use a 4-byte big-endian
  length prefix followed by UTF-8 JSON;
- message bindings (XPC, Binder, D-Bus) keep the native message boundary and
  MUST NOT add a length prefix;
- neither frame may exceed 8 MiB.
"""

from __future__ import annotations

import json
import struct
from enum import Enum

from .errors import OsapError

#: Inclusive upper bound for one frame or message (§7.9).
MAX_FRAME_BYTES = 8 * 1024 * 1024

HEADER_BYTES = 4


class Binding(str, Enum):
    """The two transport kinds a binding may declare (§7.10)."""

    STREAM = "stream"
    MESSAGE = "message"


def measure(message: object) -> int:
    """Return the UTF-8 JSON size of one message."""

    return len(
        json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )


def check_size(size: int) -> int:
    """Reject sizes above the 8 MiB bound; return the size otherwise."""

    if size > MAX_FRAME_BYTES:
        raise OsapError(
            "TRANSPORT_FRAME_TOO_LARGE",
            f"frame is {size} bytes, limit is {MAX_FRAME_BYTES}",
            details={"size": size, "limit": MAX_FRAME_BYTES},
        )
    return size


def encode_stream(message: object) -> bytes:
    """Encode one message with a 4-byte big-endian length prefix."""

    payload = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    check_size(len(payload))
    return struct.pack(">I", len(payload)) + payload


def decode_stream(buffer: bytes) -> tuple[list[dict], bytes]:
    """Split a stream buffer into complete messages and the remaining bytes."""

    messages: list[dict] = []
    while len(buffer) >= HEADER_BYTES:
        (length,) = struct.unpack(">I", buffer[:HEADER_BYTES])
        check_size(length)
        end = HEADER_BYTES + length
        if len(buffer) < end:
            break
        payload = buffer[HEADER_BYTES:end]
        try:
            messages.append(json.loads(payload.decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OsapError("SCHEMA_INVALID", f"frame is not UTF-8 JSON: {exc}") from exc
        buffer = buffer[end:]
    return messages, buffer


def encode_message(message: object) -> object:
    """Pass one message through unchanged, enforcing only the size bound."""

    check_size(measure(message))
    return message


def encode(binding: Binding, message: object):
    """Encode for the declared binding."""

    if binding == Binding.STREAM:
        return encode_stream(message)
    return encode_message(message)
