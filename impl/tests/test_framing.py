# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for the framing bindings (standard.md §7.9)."""

import unittest

from osap import OsapError, framing


class StreamBindingTests(unittest.TestCase):
    def test_round_trip(self):
        message = {"osap": "0.1", "id": "msg_1", "type": "hello"}
        encoded = framing.encode_stream(message)
        decoded, remainder = framing.decode_stream(encoded)
        self.assertEqual(decoded, [message])
        self.assertEqual(remainder, b"")

    def test_length_prefix_is_big_endian(self):
        encoded = framing.encode_stream({"a": 1})
        self.assertEqual(encoded[:4], len(encoded[4:]).to_bytes(4, "big"))

    def test_split_buffer_is_buffered(self):
        encoded = framing.encode_stream({"a": 1})
        decoded, remainder = framing.decode_stream(encoded[:-2])
        self.assertEqual(decoded, [])
        self.assertEqual(remainder, encoded[:-2])

    def test_multiple_frames(self):
        first = framing.encode_stream({"n": 1})
        second = framing.encode_stream({"n": 2})
        decoded, _ = framing.decode_stream(first + second)
        self.assertEqual(decoded, [{"n": 1}, {"n": 2}])

    def test_non_json_payload_is_schema_invalid(self):
        payload = b"not json"
        frame = len(payload).to_bytes(4, "big") + payload
        with self.assertRaises(OsapError) as caught:
            framing.decode_stream(frame)
        self.assertEqual(caught.exception.code, "SCHEMA_INVALID")


class MessageBindingTests(unittest.TestCase):
    def test_no_length_prefix(self):
        message = {"osap": "0.1", "id": "msg_1", "type": "hello"}
        self.assertIs(framing.encode_message(message), message)


class SizeLimitTests(unittest.TestCase):
    def test_exactly_eight_mib_is_accepted(self):
        self.assertEqual(framing.check_size(framing.MAX_FRAME_BYTES), framing.MAX_FRAME_BYTES)

    def test_above_eight_mib_is_rejected(self):
        with self.assertRaises(OsapError) as caught:
            framing.check_size(framing.MAX_FRAME_BYTES + 1)
        self.assertEqual(caught.exception.code, "TRANSPORT_FRAME_TOO_LARGE")
        self.assertFalse(caught.exception.retryable)

    def test_stream_encoder_rejects_oversized_payload(self):
        with self.assertRaises(OsapError) as caught:
            framing.encode_stream({"blob": "x" * (framing.MAX_FRAME_BYTES + 1)})
        self.assertEqual(caught.exception.code, "TRANSPORT_FRAME_TOO_LARGE")


if __name__ == "__main__":
    unittest.main()
