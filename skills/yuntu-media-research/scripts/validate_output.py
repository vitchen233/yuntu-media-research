#!/usr/bin/env python3
"""Validate the minimum evidence chain of a media research output."""

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_FILES = ["brief.json", "source_manifest.jsonl", "works.jsonl", "topic_cards.jsonl"]
TOPIC_FIELDS = ["topic_id", "title", "target_audience", "audience_task", "visible_result", "shooting_task", "source_ids", "benchmark_urls", "tailwind_mode", "difference", "opening_direction", "delivery_asset", "material_acquisition", "readiness"]


def rows(path):
    return [(number, json.loads(line)) for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1) if line.strip()]


def valid_url(value):
    parsed = urlparse(str(value))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate(root):
    errors = [f"missing file: {name}" for name in REQUIRED_FILES if not (root / name).is_file()]
    if errors:
        return errors
    source_ids = set()
    for line, row in rows(root / "source_manifest.jsonl"):
        source_id = row.get("source_id")
        if not source_id or source_id in source_ids:
            errors.append(f"source_manifest.jsonl:{line}: missing or duplicate source_id")
        source_ids.add(source_id)
        if not valid_url(row.get("url")):
            errors.append(f"source_manifest.jsonl:{line}: invalid url")
    linked_files = ["works.jsonl"]
    if (root / "audience_questions.jsonl").is_file():
        linked_files.append("audience_questions.jsonl")
    for filename in linked_files:
        for line, row in rows(root / filename):
            if row.get("source_id") not in source_ids:
                errors.append(f"{filename}:{line}: unknown source_id")
    for line, row in rows(root / "topic_cards.jsonl"):
        for field in TOPIC_FIELDS:
            if field not in row or row[field] in (None, "", []):
                errors.append(f"topic_cards.jsonl:{line}: missing {field}")
        for source_id in row.get("source_ids", []):
            if source_id not in source_ids:
                errors.append(f"topic_cards.jsonl:{line}: unknown source_id {source_id}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    args = parser.parse_args()
    errors = validate(Path(args.root))
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("VALIDATION PASSED")


if __name__ == "__main__":
    main()
