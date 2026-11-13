# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Reference implementation of an OSAP 0.1 Bus subset.

The package currently covers milestone M2.1: the envelope, the error model,
and both framing bindings from standard.md §7.1, §7.7, §7.9, and §7.10.
Later milestones add identity, capabilities, consent, and the task model.
"""

from .bus import Bus
from .clock import Deadline
from .envelope import KNOWN_TYPES, SUPPORTED_MAJOR, validate
from .errors import STANDARD_CODES, OsapError
from .framing import MAX_FRAME_BYTES, Binding
from .idempotency import IdempotencyIndex

__all__ = [
    "Binding",
    "Bus",
    "Deadline",
    "IdempotencyIndex",
    "KNOWN_TYPES",
    "MAX_FRAME_BYTES",
    "OsapError",
    "STANDARD_CODES",
    "SUPPORTED_MAJOR",
    "validate",
]
