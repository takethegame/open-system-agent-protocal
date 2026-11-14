# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Reference implementation of an OSAP 0.1 Bus subset.

Covered so far:

- M2.1: envelope, error model, stream and message framing, handshake,
  idempotency, and monotonic-clock deadlines (standard.md §7.1–§7.10);
- M2.2: Ed25519 manifest signatures, agent registration, reserved namespaces,
  and the registry subset (§4, §6);
- M2.3: capability tokens, attenuation, binding, revocation (§5.1-§5.6);
- M2.4: consent receipts and capability linkage (§5.8);
- M2.5: task tree, budgets, cancellation, results, handoff (§8).
"""

from . import capability, consent, crypto, identity, registry, schema, task
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
    "capability",
    "consent",
    "crypto",
    "identity",
    "registry",
    "schema",
    "task",
    "validate",
]
