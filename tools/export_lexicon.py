#!/usr/bin/env python3
"""Export structured MCP data from the authoritative LaTeX tables.

Usage:
  python tools/export_lexicon.py
  python tools/export_lexicon.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "purepersian_mcp" / "lexicon.json"
SOURCES = ("persian.tex", "adverbs.tex")


def generate() -> dict:
    entries: list[dict] = []
    for source in SOURCES:
        category = ""
        inside_table = False
        for line in (ROOT / source).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            heading = re.fullmatch(r"\\section\*\{(.+)\}", line)
            if heading:
                category = heading.group(1)
                continue
            if line.startswith(r"\begin{longtable}"):
                inside_table = True
                continue
            if line.startswith(r"\end{longtable}"):
                inside_table = False
                continue
            if not (inside_table and " & " in line and line.endswith("\\\\")):
                continue
            cells = line[:-2].strip().split(" & ")
            if len(cells) != 4:
                raise ValueError(f"{source}: Expected four columns: {line}")
            term, equivalents, english, usage = cells
            if term == "واژهٔ رایج":
                continue
            if not all((term, equivalents, english, usage)):
                raise ValueError(f"{source}: Missing field: {line}")
            english = re.sub(r"^\\textenglish\{(.+)\}$", r"\1", english)
            entry = {
                "id": f"{'main' if source == 'persian.tex' else 'adverbs'}:{category}:{term}",
                "term": term,
                "equivalents": [s.strip() for s in equivalents.split("/") if s.strip()],
                "english": english,
                "usage": usage,
                "category": category,
                "source": source,
                "review_status": "legacy" if source == "persian.tex" else "editorial",
            }
            if not entry["equivalents"] or not category:
                raise ValueError(f"{source}: Invalid entry: {line}")
            entries.append(entry)

    ids = [e["id"] for e in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate entry IDs detected")
    if not entries:
        raise ValueError("No glossary entries were parsed")
    return {
        "schema_version": "1.0.0",
        "language": "fa",
        "source_of_truth": list(SOURCES),
        "disclaimer": "برابرها پیشنهادهای وابسته به بافت‌اند، نه دستورهای جایگزینی خودکار. مدخل‌های قدیمی هنوز نیازمند بازبینی واژه‌شناختی هستند.",
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if checked-in JSON is out of sync")
    args = parser.parse_args()
    generated = generate()
    if args.check:
        try:
            actual = json.loads(DEST.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Cannot read lexicon JSON: {exc}", file=sys.stderr)
            return 1
        if actual != generated:
            print("The JSON lexicon is stale. Run python tools/export_lexicon.py", file=sys.stderr)
            return 1
        print(f"Verified {len(generated['entries'])} glossary entries")
        return 0
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(generated['entries'])} entries to {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
