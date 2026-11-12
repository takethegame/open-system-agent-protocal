#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Load, validate, and run OSAP conformance cases.

Usage:
    python3 tools/conformance_run.py --stub
    python3 tools/conformance_run.py --impl path/to/adapter.py --format md

An adapter is a Python file exposing:

    def conformance_check(case: dict, documents: dict) -> dict:
        '''Return {"outcome": "accept"|"reject", "error": "...", "state": {...}}.'''

`documents` contains `primary` (the mutated input.ref fixture) and `context`
(the mutated context fixtures, in order). The runner applies all declared
mutations before calling the adapter.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "conformance" / "cases"
SCHEMA_DIRS = [ROOT / "schemas", ROOT / "conformance"]


class Skip(Exception):
    """Raised by an adapter when a case is out of its scope."""


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def build_registry() -> Registry:
    registry = Registry()
    for directory in SCHEMA_DIRS:
        for path in sorted(directory.glob("*.schema.json")):
            schema = load(path)
            registry = registry.with_resource(
                schema["$id"],
                Resource.from_contents(schema, default_specification=DRAFT202012),
            )
    return registry


def load_suites(case_dir: Path, registry: Registry) -> list[tuple[Path, dict]]:
    suite_schema = load(SCHEMA_DIRS[1] / "suite.schema.json")
    validator = Draft202012Validator(
        suite_schema, registry=registry, format_checker=FormatChecker()
    )
    suites = []
    for path in sorted(case_dir.glob("*.json")):
        suite = load(path)
        errors = sorted(validator.iter_errors(suite), key=lambda e: list(e.path))
        if errors:
            details = "; ".join(
                f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}"
                for e in errors
            )
            raise SystemExit(f"{path.name}: invalid suite: {details}")
        suites.append((path, suite))
    if not suites:
        raise SystemExit(f"no case files found in {case_dir}")
    return suites


def check_ids(suites: list[tuple[Path, dict]]) -> None:
    seen: dict[str, str] = {}
    problems = []
    for path, suite in suites:
        for case in suite["cases"]:
            if case["level"] != suite["level"]:
                problems.append(
                    f"{path.name}: case {case['id']} level {case['level']} != suite {suite['level']}"
                )
            if case["id"] in seen:
                problems.append(
                    f"{path.name}: duplicate case id {case['id']} (also in {seen[case['id']]})"
                )
            else:
                seen[case["id"]] = path.name
    if problems:
        raise SystemExit("FAIL\n  - " + "\n  - ".join(problems))


# --- JSON Pointer (RFC 6901) ------------------------------------------------


def parse_pointer(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer: {pointer!r}")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def resolve(document, pointer: str):
    node = document
    for token in parse_pointer(pointer):
        if isinstance(node, list):
            node = node[int(token)]
        else:
            node = node[token]
    return node


def apply_mutation(document, mutation: dict):
    tokens = parse_pointer(mutation["path"])
    if not tokens:
        raise ValueError("mutation on the document root is not supported")
    parent = document
    for token in tokens[:-1]:
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    last = tokens[-1]
    op = mutation["op"]

    if op == "remove":
        if isinstance(parent, list):
            del parent[int(last)]
        else:
            del parent[last]
        return document

    if op == "add":
        if isinstance(parent, list):
            if last == "-":
                parent.append(mutation["value"])
            else:
                parent.insert(int(last), mutation["value"])
        else:
            parent[last] = mutation["value"]
        return document

    if op == "replace":
        if isinstance(parent, list):
            parent[int(last)] = mutation["value"]
        else:
            if last not in parent:
                raise KeyError(f"replace target does not exist: {mutation['path']}")
            parent[last] = mutation["value"]
        return document

    if op == "extend":
        current = resolve(document, mutation["path"])
        if not isinstance(current, list) or not isinstance(mutation.get("value"), list):
            raise ValueError(f"extend requires an array target and array value: {mutation['path']}")
        current.extend(mutation["value"])
        return document

    if op == "truncate":
        current = resolve(document, mutation["path"])
        if not isinstance(current, list) or not isinstance(mutation.get("value"), int):
            raise ValueError(f"truncate requires an array target and integer value: {mutation['path']}")
        del current[mutation["value"] :]
        return document

    raise ValueError(f"unsupported mutation op: {op}")


def build_documents(case: dict, case_file: Path) -> dict:
    source = case.get("input") or {}
    documents: dict = {"primary": None, "context": []}

    def materialise(relative: str):
        path = (case_file.parent / relative).resolve()
        if not path.exists():
            raise SystemExit(f"{case['id']}: fixture not found: {relative}")
        return load(path)

    if "ref" in source:
        documents["primary"] = materialise(source["ref"])
    documents["context"] = [materialise(item) for item in source.get("context", [])]
    for mutation in source.get("mutations", []):
        if documents["primary"] is None:
            raise SystemExit(f"{case['id']}: mutations need input.ref")
        documents["primary"] = apply_mutation(documents["primary"], mutation)
    return documents


# --- Execution --------------------------------------------------------------


def load_adapter(path: Path):
    spec = importlib.util.spec_from_file_location("osap_conformance_adapter", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load adapter: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "conformance_check"):
        raise SystemExit(f"adapter {path} does not define conformance_check()")
    return module.conformance_check


def evaluate(expect: dict, actual: dict) -> tuple[bool, str]:
    if expect["outcome"] == "observe":
        return True, "observed"
    if actual.get("outcome") != expect["outcome"]:
        return False, f"expected outcome {expect['outcome']}, got {actual.get('outcome')}"
    if expect["outcome"] == "reject" and actual.get("error") != expect.get("error"):
        return False, f"expected error {expect.get('error')}, got {actual.get('error')}"
    for key, value in expect.get("state", {}).items():
        if actual.get("state", {}).get(key) != value:
            return False, f"expected state.{key}={value!r}, got {actual.get('state', {}).get(key)!r}"
    return True, "matched"


def run_case(case: dict, case_file: Path, adapter) -> dict:
    result = {
        "id": case["id"],
        "level": case["level"],
        "expected": case["expect"],
    }
    if case.get("mode", "automated") == "manual":
        return {**result, "status": "skip", "reason": "manual case: run the steps by hand"}
    if adapter is None:
        return {**result, "status": "skip", "reason": "no implementation adapter (--stub)"}
    try:
        documents = build_documents(case, case_file)
        actual = adapter(case, documents) or {}
    except Skip as exc:
        return {**result, "status": "skip", "reason": str(exc) or "adapter skipped"}
    except Exception as exc:  # adapter failure is a conformance failure
        return {**result, "status": "fail", "reason": f"adapter error: {exc}"}

    if actual.get("outcome") == "skip":
        return {
            **result,
            "status": "skip",
            "reason": actual.get("reason", "adapter skipped"),
        }

    passed, reason = evaluate(case["expect"], actual)
    return {
        **result,
        "status": "pass" if passed else "fail",
        "actual": actual,
        "reason": reason,
    }


def summarise(results: list[dict]) -> dict:
    return {
        "total": len(results),
        "pass": sum(r["status"] == "pass" for r in results),
        "fail": sum(r["status"] == "fail" for r in results),
        "skip": sum(r["status"] == "skip" for r in results),
    }


def render_text(results: list[dict], summary: dict, levels: list[str]) -> str:
    lines = []
    for result in results:
        suffix = f" ({result['reason']})" if result.get("reason") else ""
        lines.append(f"{result['id']:<6} {result['status'].upper():<5}{suffix}")
    lines.append("")
    lines.append(
        f"{summary['total']} cases [{', '.join(levels)}]: "
        f"{summary['pass']} pass, {summary['fail']} fail, {summary['skip']} skip"
    )
    return "\n".join(lines)


def render_markdown(results: list[dict], summary: dict, levels: list[str]) -> str:
    lines = [
        "# OSAP Conformance Report",
        "",
        f"- Levels: {', '.join(levels)}",
        f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "| Case | Level | Status | Reason |",
        "|---|---|---|---|",
    ]
    for result in results:
        reason = (result.get("reason") or "").replace("|", "\\|")
        lines.append(
            f"| {result['id']} | {result['level']} | {result['status']} | {reason} |"
        )
    lines += [
        "",
        f"**Summary**: {summary['total']} total, {summary['pass']} pass, "
        f"{summary['fail']} fail, {summary['skip']} skip.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=CASE_DIR, help="case directory")
    parser.add_argument("--impl", type=Path, help="adapter module exposing conformance_check()")
    parser.add_argument("--stub", action="store_true", help="load and validate cases without an adapter")
    parser.add_argument("--level", default="", help="comma-separated levels, e.g. C0,C3")
    parser.add_argument("--format", choices=["text", "json", "md"], default="text")
    parser.add_argument("--out", type=Path, help="write the report to a file")
    args = parser.parse_args()

    if args.impl and args.stub:
        raise SystemExit("--impl and --stub are mutually exclusive")
    if not args.impl:
        args.stub = True

    registry = build_registry()
    suites = load_suites(args.cases, registry)
    check_ids(suites)

    wanted = {item.strip().upper() for item in args.level.split(",") if item.strip()}
    adapter = load_adapter(args.impl) if args.impl else None

    results = []
    for path, suite in suites:
        if wanted and suite["level"] not in wanted:
            continue
        for case in suite["cases"]:
            results.append(run_case(case, path, adapter))

    if not results:
        raise SystemExit("no cases selected")

    summary = summarise(results)
    levels = [suite["level"] for _, suite in suites if not wanted or suite["level"] in wanted]

    if args.format == "json":
        report = {
            "osap": "0.1",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "cases": results,
            "summary": summary,
        }
        output = json.dumps(report, indent=2, ensure_ascii=False)
    elif args.format == "md":
        output = render_markdown(results, summary, levels)
    else:
        output = render_text(results, summary, levels)

    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
        if args.format == "text":
            print(output)
        else:
            print(f"report written to {args.out}")
    else:
        print(output)

    return 1 if summary["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
