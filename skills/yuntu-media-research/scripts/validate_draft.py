#!/usr/bin/env python3
"""Validate a research-grounded draft bundle."""

import argparse
import json
from pathlib import Path


REQUIRED_FILES = ("selected_topic.md", "draft.md", "draft_source_map.json", "audit.md")
PLACEHOLDERS = ("{{", "}}", "TODO", "待补充", "示例标题")


def validate(root):
    root = Path(root)
    errors = []
    for name in REQUIRED_FILES:
        if not (root / name).is_file():
            errors.append(f"missing file: {name}")
    draft_path = root / "draft.md"
    if draft_path.is_file():
        draft = draft_path.read_text(encoding="utf-8")
        for marker in PLACEHOLDERS:
            if marker in draft:
                errors.append(f"draft contains placeholder: {marker}")
    map_path = root / "draft_source_map.json"
    if map_path.is_file():
        try:
            source_map = json.loads(map_path.read_text(encoding="utf-8"))
            claims = source_map.get("claims", []) if isinstance(source_map, dict) else []
            if not claims:
                errors.append("draft source map has no claims")
            for index, claim in enumerate(claims, 1):
                if not claim.get("basis"):
                    errors.append(f"claim {index} has no basis")
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid draft source map: {exc}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", help="Research output directory containing the draft bundle")
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Draft bundle is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
