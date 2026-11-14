# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Unit tests for the idempotency index (standard.md §7.8)."""

import unittest

from osap.idempotency import IdempotencyIndex


class IdempotencyTests(unittest.TestCase):
    def setUp(self):
        self.index = IdempotencyIndex()
        self.calls = 0

    def effect(self, result=None):
        self.calls += 1
        return result

    def test_first_call_executes(self):
        result, replayed = self.index.execute_once("msg_1", lambda: self.effect("ok"))
        self.assertEqual(result, "ok")
        self.assertFalse(replayed)
        self.assertEqual(self.calls, 1)

    def test_second_call_returns_the_cached_result(self):
        self.index.execute_once("msg_1", lambda: self.effect("ok"))
        result, replayed = self.index.execute_once("msg_1", lambda: self.effect("again"))
        self.assertEqual(result, "ok")
        self.assertTrue(replayed)
        self.assertEqual(self.calls, 1)

    def test_none_result_is_still_cached(self):
        self.index.execute_once("msg_1", self.effect)
        result, replayed = self.index.execute_once("msg_1", self.effect)
        self.assertIsNone(result)
        self.assertTrue(replayed)
        self.assertEqual(self.calls, 1)

    def test_distinct_ids_execute_separately(self):
        self.index.execute_once("msg_1", self.effect)
        self.index.execute_once("msg_2", self.effect)
        self.assertEqual(self.calls, 2)
        self.assertEqual(len(self.index), 2)

    def test_lookup_is_none_for_an_unknown_id(self):
        self.assertIsNone(self.index.lookup("msg_missing"))

    def test_forget_forces_the_next_execution(self):
        self.index.execute_once("msg_1", self.effect)
        self.index.forget("msg_1")
        self.index.execute_once("msg_1", self.effect)
        self.assertEqual(self.calls, 2)

    def test_clear_forces_the_next_execution(self):
        self.index.execute_once("msg_1", self.effect)
        self.index.clear()
        self.index.execute_once("msg_1", self.effect)
        self.assertEqual(self.calls, 2)


if __name__ == "__main__":
    unittest.main()
