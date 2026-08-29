#!/usr/bin/env python3
"""Validate report JSON before it is rendered or recorded."""

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


REPORT_TYPES = {"topic-research", "creator-analysis", "content-structure-analysis"}
COMMON = ("report_type", "title", "summary", "generated_at", "method", "limitations")


def valid_url(value):
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and parsed.netloc != "example.com"


def validate(data):
    errors = [f"missing {field}" for field in COMMON if data.get(field) in (None, "", [])]
    report_type = data.get("report_type")
    if report_type not in REPORT_TYPES:
        errors.append("unsupported report_type")
        return errors
    serialized = json.dumps(data, ensure_ascii=False).lower()
    for token in ("todo", "待填写", "示例数据", "your_api_key"):
        if token.lower() in serialized:
            errors.append(f"placeholder token found: {token}")
    if report_type == "topic-research":
        if len(data.get("candidates", [])) != 3:
            errors.append("topic-research requires exactly 3 candidates")
        sources = data.get("sources", [])
    elif report_type == "creator-analysis":
        if not data.get("content_map"):
            errors.append("creator-analysis requires content_map")
        sources = data.get("sources", [])
    else:
        if len(data.get("stages", [])) < 3:
            errors.append("content-structure-analysis requires at least 3 stages")
        if not valid_url(data.get("source_url")):
            errors.append("content-structure-analysis requires a valid source_url")
        sources = []
    if report_type != "content-structure-analysis" and not sources:
        errors.append(f"{report_type} requires at least one source")
    for index, source in enumerate(sources, 1):
        if not valid_url(source.get("url")):
            errors.append(f"source {index} has invalid url")
        if not source.get("title"):
            errors.append(f"source {index} is missing title")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        print("REPORT VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("REPORT VALIDATION PASSED")


if __name__ == "__main__":
    main()
