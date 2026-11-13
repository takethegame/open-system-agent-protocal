# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Shared JSON Schema loading for protocol documents.

`schemas/` is the single source of truth; this module only wires the schemas
into a resolver and maps validation failures to `SCHEMA_INVALID`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry as SchemaRegistry
from referencing import Resource
from referencing.jsonschema import DRAFT202012

from .errors import OsapError

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


@lru_cache(maxsize=1)
def _registry() -> SchemaRegistry:
    registry = SchemaRegistry()
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        registry = registry.with_resource(
            schema["$id"],
            Resource.from_contents(schema, default_specification=DRAFT202012),
        )
    return registry


@lru_cache(maxsize=None)
def validator(name: str) -> Draft202012Validator:
    """Return a validator for `schemas/<name>`."""

    schema = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=_registry(), format_checker=FormatChecker())


def pointer(parts) -> str:
    return "/" + "/".join(str(part) for part in parts) if parts else "<root>"


def validate(name: str, document: object, *, code: str = "SCHEMA_INVALID") -> None:
    """Validate `document` against `schemas/<name>` or raise `OsapError`."""

    errors = sorted(validator(name).iter_errors(document), key=lambda error: list(error.path))
    if not errors:
        return
    first = errors[0]
    raise OsapError(
        code,
        f"{pointer(first.path)}: {first.message}",
        details={"path": pointer(first.path), "schema": name},
    )
