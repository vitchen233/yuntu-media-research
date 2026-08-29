#!/usr/bin/env python3
"""Re-filter an existing collection without making new RedFox requests."""

import argparse
import importlib.util
import json
from pathlib import Path


def load_collector():
    path = Path(__file__).with_name("redfox_collect.py")
    spec = importlib.util.spec_from_file_location("redfox_collect", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_rows(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    root = Path(args.root)
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    collector = load_collector()
    source_path = root / "source_manifest_collected.jsonl"
    works_path = root / "works_collected.jsonl"
    if not source_path.exists():
        source_path = root / "source_manifest.jsonl"
    if not works_path.exists():
        works_path = root / "works.jsonl"
    manifest = load_rows(source_path)
    works = load_rows(works_path)
    relevant_manifest, relevant_works, exclusions = collector.filter_pairs(manifest, works, config.get("required_any_groups", []))
    if source_path.name == "source_manifest.jsonl":
        write_rows(root / "source_manifest_collected.jsonl", manifest)
    if works_path.name == "works.jsonl":
        write_rows(root / "works_collected.jsonl", works)
    write_rows(root / "source_manifest.jsonl", relevant_manifest)
    write_rows(root / "works.jsonl", relevant_works)
    write_rows(root / "relevance_exclusions.jsonl", exclusions)
    print(json.dumps({"collected": len(works), "relevant": len(relevant_works), "excluded": len(exclusions)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
