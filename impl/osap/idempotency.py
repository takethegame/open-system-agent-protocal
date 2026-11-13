# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Idempotency index from standard.md §7.8.

A repeated `id` MUST return the cached result or `DUPLICATE`; it MUST NOT
execute side effects twice, including across a Bus restart. This in-memory
index is the reference implementation's stand-in for a persistent store.
"""

from __future__ import annotations

from typing import Any, Callable


class IdempotencyIndex:
    """Cache of results keyed by message id."""

    def __init__(self) -> None:
        self._entries: dict[str, Any] = {}

    def __len__(self) -> int:
        return len(self._entries)

    def lookup(self, message_id: str) -> Any | None:
        """Return the cached result, or None when the id is new."""

        return self._entries.get(message_id)

    def remember(self, message_id: str, result: Any) -> Any:
        self._entries[message_id] = result
        return result

    def execute_once(self, message_id: str, action: Callable[[], Any]) -> tuple[Any, bool]:
        """Run `action` only for a new id; return `(result, replayed)`."""

        cached = self._entries.get(message_id)
        if cached is not None:
            return cached, True
        return self.remember(message_id, action()), False

    def forget(self, message_id: str) -> None:
        self._entries.pop(message_id, None)

    def clear(self) -> None:
        self._entries.clear()
