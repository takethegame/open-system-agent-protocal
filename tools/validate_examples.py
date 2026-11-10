#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Validate OSAP example documents against the JSON Schemas.

Usage:
    python3 tools/validate_examples.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "examples"

# Examples that map 1:1 to a document schema.
MAPPING = {
    "manifest.json": "manifest.schema.json",
    "capability.json": "capability.schema.json",
    "capability-record.json": "capability-record.schema.json",
    "task.json": "task.schema.json",
    "consent-receipt.json": "consent-receipt.schema.json",
    "audit-event.json": "audit-event.schema.json",
    "discovery-request.json": "envelope.schema.json",
    "discovery-result.json": "envelope.schema.json",
    "request.json": "envelope.schema.json",
    "result.json": "envelope.schema.json",
    "delegate.json": "envelope.schema.json",
    "handoff.json": "envelope.schema.json",
    "consent-request.json": "envelope.schema.json",
}

# Envelope examples whose body.data is validated against a payload schema.
PAYLOAD_SCHEMAS = {
    "osap.discover/v1": "discover.schema.json",
    "osap.discover.result/v1": "discover-result.schema.json",
    "osap.delegate/v1": "delegate.schema.json",
    "osap.consent.request/v1": "consent-request.schema.json",
    "osap.handoff/v1": "handoff.schema.json",
}


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def build_registry() -> Registry:
    """Register every schema by $id so cross-schema $ref resolves."""
    registry = Registry()
    for path in sorted(SCHEMAS.glob("*.schema.json")):
        schema = load(path)
        resource = Resource.from_contents(schema, default_specification=DRAFT202012)
        registry = registry.with_resource(schema["$id"], resource)
    return registry


def validate(instance: dict, schema: dict, registry: Registry) -> list[str]:
    validator = Draft202012Validator(
        schema, registry=registry, format_checker=FormatChecker()
    )
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    return [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors]


def main() -> int:
    failures: list[str] = []
    checks = 0
    registry = build_registry()

    for example_name, schema_name in MAPPING.items():
        example_path = EXAMPLES / example_name
        if not example_path.exists():
            failures.append(f"{example_name}: missing example")
            continue
        instance = load(example_path)
        schema = load(SCHEMAS / schema_name)
        checks += 1
        for error in validate(instance, schema, registry):
            failures.append(f"{example_name} [{schema_name}] {error}")

        # Envelope -> payload validation.
        schema_id = instance.get("body", {}).get("schema")
        payload_name = PAYLOAD_SCHEMAS.get(schema_id)
        if payload_name:
            payload_schema = load(SCHEMAS / payload_name)
            checks += 1
            for error in validate(instance["body"]["data"], payload_schema, registry):
                failures.append(f"{example_name} [{payload_name}] {error}")

    # Cross-document check: delegated capability must itself be valid.
    for example_name in ("delegate.json", "handoff.json"):
        instance = load(EXAMPLES / example_name)
        delegated = instance["body"]["data"]["delegated_capability"]
        capability = load(SCHEMAS / "capability.schema.json")
        checks += 1
        for error in validate(delegated, capability, registry):
            failures.append(f"{example_name} [capability.schema.json] {error}")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"OK: {checks} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
