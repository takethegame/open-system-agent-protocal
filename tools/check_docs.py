#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Repository-level documentation checks.

Verifies that:
  - every fenced ```json block parses;
  - every Markdown file has balanced code fences;
  - every relative link resolves;
  - Chinese originals and English translations have matching heading levels
    and code-fence counts;
  - no personal identifiers or local paths leaked into tracked text.

Usage:
    python3 tools/check_docs.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".idea"}

# Pairs that must stay structurally aligned. Missing files are reported.
PAIRS = [
    ("README.md", "README.en.md"),
    ("GOVERNANCE.md", "GOVERNANCE.en.md"),
    ("CONTRIBUTING.md", "CONTRIBUTING.en.md"),
    ("SECURITY.md", "SECURITY.en.md"),
    ("docs/standard.md", "docs/standard.en.md"),
    ("docs/conformance.md", "docs/conformance.en.md"),
    ("docs/design-draft.md", "docs/design-draft.en.md"),
    ("docs/prior-art.md", "docs/prior-art.en.md"),
]

# Personal identifiers and machine-specific paths that must never ship.
FORBIDDEN = ["zengyunhao", "macbook-pro", "zhangsan", "张三", "/Users/"]

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s", re.MULTILINE)
FENCE_RE = re.compile(r"^\s*```", re.MULTILINE)


def markdown_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def strip_fences(text: str) -> str:
    """Drop fenced code blocks so their content is not linted as prose."""
    out, in_fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def check_file(path: Path) -> tuple[int, list[str]]:
    failures: list[str] = []
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    checks = 0

    checks += 1
    if text.count("```") % 2:
        failures.append(f"{rel}: unbalanced code fences")

    checks += 1
    for index, block in enumerate(re.finditer(r"```json\n(.*?)```", text, re.S), 1):
        try:
            json.loads(block.group(1))
        except json.JSONDecodeError as exc:
            line = text[: block.start()].count("\n") + 1
            failures.append(f"{rel}:{line}: json block #{index} does not parse: {exc}")

    checks += 1
    prose = strip_fences(text)
    for match in LINK_RE.finditer(prose):
        target = match.group(1).split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if not (path.parent / target).resolve().exists():
            line = prose[: match.start()].count("\n") + 1
            failures.append(f"{rel}:{line}: broken link -> {match.group(1)}")

    checks += 1
    lowered = text.lower()
    for needle in FORBIDDEN:
        if needle.lower() in lowered:
            failures.append(f"{rel}: contains forbidden string {needle!r}")

    return checks, failures


def check_pair(original: Path, translation: Path) -> tuple[int, list[str]]:
    failures: list[str] = []
    if not original.exists() or not translation.exists():
        return 0, [f"missing pair: {original.name} / {translation.name}"]

    checks = 1
    a = original.read_text(encoding="utf-8")
    b = translation.read_text(encoding="utf-8")

    levels_a = [len(m.group(1)) for m in HEADING_RE.finditer(strip_fences(a))]
    levels_b = [len(m.group(1)) for m in HEADING_RE.finditer(strip_fences(b))]
    checks += 1
    if levels_a != levels_b:
        failures.append(
            f"{translation.name}: heading levels differ from {original.name} "
            f"({len(levels_a)} vs {len(levels_b)} headings)"
        )

    checks += 1
    fences_a = len(FENCE_RE.findall(a))
    fences_b = len(FENCE_RE.findall(b))
    if fences_a != fences_b:
        failures.append(
            f"{translation.name}: code fence count differs from {original.name} "
            f"({fences_a} vs {fences_b})"
        )

    return checks, failures


def main() -> int:
    failures: list[str] = []
    checks = 0

    files = markdown_files()
    for path in files:
        file_checks, file_failures = check_file(path)
        checks += file_checks
        failures.extend(file_failures)

    for original_name, translation_name in PAIRS:
        pair_checks, pair_failures = check_pair(
            ROOT / original_name, ROOT / translation_name
        )
        checks += pair_checks
        failures.extend(pair_failures)

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"OK: {checks} checks passed across {len(files)} Markdown files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
