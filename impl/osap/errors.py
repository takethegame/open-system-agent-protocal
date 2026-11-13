# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Error model from standard.md §7.7.

Every rejection carries one of the standard codes below. A domain may add
codes in the reserved prefixes, or use its own namespace; `is_standard()`
tells the two apart so reports can flag extensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Codes defined by the standard. Keep in sync with docs/standard.md §7.7.
STANDARD_CODES = frozenset(
    {
        "TRANSPORT_HANDSHAKE_REQUIRED",
        "TRANSPORT_VERSION_UNSUPPORTED",
        "TRANSPORT_FRAME_TOO_LARGE",
        "TRANSPORT_CLOCK_SKEW",
        "SCHEMA_UNSUPPORTED",
        "SCHEMA_INVALID",
        "AUTH_DENIED",
        "ROUTING_AMBIGUOUS",
        "ROUTING_NOT_FOUND",
        "CAPABILITY_AUDIENCE_MISMATCH",
        "CAPABILITY_SUBJECT_MISMATCH",
        "CAPABILITY_TASK_MISMATCH",
        "CAPABILITY_ATTENUATION_INVALID",
        "CAPABILITY_REVOKED",
        "POLICY_DENIED",
        "POLICY_CONSENT_REQUIRED",
        "POLICY_CONSENT_EXPIRED",
        "POLICY_CONSENT_SCOPE_MISMATCH",
        "TASK_BUDGET_EXCEEDED",
        "CONTEXT_DENIED",
        "CONTEXT_EXPIRED",
        "CONTEXT_NOT_FOUND",
        "DUPLICATE",
        "RATE_LIMIT",
        "TIMEOUT",
        "CANCELLED",
        "INTERNAL",
    }
)

#: Codes that a caller may retry, per the "可重试" column of §7.7.
RETRYABLE_CODES = frozenset({"DUPLICATE", "RATE_LIMIT", "TIMEOUT", "INTERNAL"})

#: Prefixes reserved for implementation-defined codes (§7.7, last paragraph).
EXTENSION_PREFIXES = (
    "AUTH_",
    "POLICY_",
    "CAPABILITY_",
    "TASK_",
    "SCHEMA_",
    "CONTEXT_",
    "ROUTING_",
    "TRANSPORT_",
)


def is_standard(code: str) -> bool:
    """True when `code` is defined by the standard."""

    return code in STANDARD_CODES


def is_extension(code: str) -> bool:
    """True when `code` uses a reserved prefix instead of a standard name."""

    return code not in STANDARD_CODES and code.startswith(EXTENSION_PREFIXES)


@dataclass
class OsapError(Exception):
    """A structured rejection, serialisable to an `osap.error/v1` body."""

    code: str
    message: str = ""
    retryable: bool | None = None
    details: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.code or not self.code.replace("_", "").isalnum():
            raise ValueError(f"invalid error code: {self.code!r}")
        if self.retryable is None:
            self.retryable = self.code in RETRYABLE_CODES
        Exception.__init__(self, f"{self.code}: {self.message}" if self.message else self.code)

    @property
    def standard(self) -> bool:
        return is_standard(self.code)

    def to_data(self) -> dict:
        """Return the `body.data` object for an `osap.error/v1` message."""

        data: dict = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.details:
            data["details"] = dict(self.details)
        return data
