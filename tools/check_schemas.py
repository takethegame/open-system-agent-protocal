#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Meta-validate every JSON Schema in schemas/.

Each schema must be valid against the JSON Schema 2020-12 metaschema, use a
unique $id in the osap namespace, and resolve all internal $ref targets.

Usage:
    python3 tools/check_schemas.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIRS = [ROOT / "schemas", ROOT / "conformance"]
EXPECTED_ID_PREFIX = "urn:osap:schema:"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    failures: list[str] = []
    checks = 0
    seen_ids: dict[str, str] = {}

    paths = sorted(
        path for directory in SCHEMA_DIRS for path in directory.glob("*.schema.json")
    )
    if not paths:
        print("FAIL: no schemas found")
        return 1

    for path in paths:
        label = path.relative_to(ROOT)
        try:
            schema = load(path)
        except json.JSONDecodeError as exc:
            failures.append(f"{label}: invalid JSON: {exc}")
            continue

        checks += 1
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # jsonschema raises SchemaError
            failures.append(f"{label}: metaschema violation: {exc}")
            continue

        checks += 1
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id.startswith(
            EXPECTED_ID_PREFIX
        ):
            failures.append(
                f"{label}: $id must start with {EXPECTED_ID_PREFIX!r}, got {schema_id!r}"
            )
        elif schema_id in seen_ids:
            failures.append(
                f"{label}: duplicate $id {schema_id!r} (also in {seen_ids[schema_id]})"
            )
        else:
            seen_ids[schema_id] = str(label)

    for path in paths:
        label = path.relative_to(ROOT)
        try:
            schema = load(path)
        except json.JSONDecodeError:
            continue
        checks += 1
        for ref in _iter_refs(schema):
            if ref.startswith("#") or ref.startswith("urn:osap:schema:"):
                continue
            failures.append(f"{label}: unsupported $ref target {ref!r}")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"OK: {checks} checks passed across {len(paths)} schemas")
    return 0


def _iter_refs(node: object):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                yield value
            else:
                yield from _iter_refs(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_refs(item)


if __name__ == "__main__":
    sys.exit(main())
