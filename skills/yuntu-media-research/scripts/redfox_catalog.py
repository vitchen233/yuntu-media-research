#!/usr/bin/env python3
"""Discover and call capabilities exposed by the installed RedFox Python SDK."""

import argparse
import importlib.metadata
import inspect
import json
import os
import sys

from redfox_runtime import has_api_key, load_env_file, write_or_print


def import_client():
    try:
        from redfox import RedFoxClient
    except ImportError as exc:
        raise RuntimeError("Install dependency: pip install redfox-python-sdk") from exc
    return RedFoxClient


def parameter_schema(parameter):
    annotation = parameter.annotation
    if annotation is inspect.Parameter.empty:
        type_name = "unknown"
    else:
        type_name = getattr(annotation, "__name__", str(annotation))
    required = parameter.default is inspect.Parameter.empty
    return {
        "name": parameter.name,
        "type": type_name,
        "required": required,
        "default": None if required else parameter.default,
    }


def operation_capabilities(method_name):
    labels = []
    rules = (
        ("search", "search"),
        ("comment", "comments"),
        ("rank", "ranking"),
        ("transcript", "transcript"),
        ("download", "download"),
        ("user", "account"),
        ("account", "account"),
        ("work", "work"),
        ("article", "work"),
        ("video", "work"),
    )
    for token, label in rules:
        if token in method_name and label not in labels:
            labels.append(label)
    return labels or ["other"]


def price_class_from_description(description):
    text = description or ""
    if "优质库" in text or "premium" in text.lower():
        return "quality"
    if "实时" in text or "realtime" in text.lower():
        return "realtime"
    if "广域库" in text:
        return "unknown"
    return "unknown"


def build_catalog():
    RedFoxClient = import_client()
    client = RedFoxClient(api_key="catalog-only")
    operations = []
    try:
        for platform in sorted(name for name in dir(client) if not name.startswith("_")):
            endpoint = getattr(client, platform)
            if not endpoint.__class__.__module__.startswith("redfox.endpoints"):
                continue
            for method_name in sorted(name for name in dir(endpoint) if not name.startswith("_")):
                method = getattr(endpoint, method_name)
                if not callable(method):
                    continue
                signature = inspect.signature(method)
                doc = inspect.getdoc(method) or ""
                operations.append({
                    "operation_id": f"sdk.{platform}.{method_name}",
                    "transport": "sdk",
                    "platform": platform,
                    "method": method_name,
                    "capabilities": operation_capabilities(method_name),
                    "parameters": [parameter_schema(p) for p in signature.parameters.values()],
                    "description": doc.splitlines()[0] if doc else "",
                    "price_class": price_class_from_description(doc),
                })
    finally:
        client.close()
    try:
        version = importlib.metadata.version("redfox-python-sdk")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"
    return {"transport": "sdk", "sdk_version": version, "operation_count": len(operations), "operations": operations}


def search_catalog(catalog, query, platform=None, capability=None, limit=20):
    tokens = [token.lower() for token in query.split() if token.strip()]
    ranked = []
    for operation in catalog["operations"]:
        if platform and operation["platform"] != platform:
            continue
        if capability and capability not in operation["capabilities"]:
            continue
        haystack = json.dumps(operation, ensure_ascii=False).lower()
        score = sum(1 for token in tokens if token in haystack)
        if not tokens:
            score = 1
        if score:
            ranked.append((score, operation["operation_id"], operation))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [operation for _, _, operation in ranked[:limit]]


def call_operation(operation_id, arguments):
    parts = operation_id.split(".")
    if len(parts) == 3 and parts[0] == "sdk":
        _, platform, method_name = parts
    elif len(parts) == 2:
        platform, method_name = parts
    else:
        raise ValueError("operation must be sdk.<platform>.<method> or <platform>.<method>")
    if not has_api_key():
        raise RuntimeError("REDFOX_API_KEY is not configured")
    RedFoxClient = import_client()
    client = RedFoxClient()
    try:
        endpoint = getattr(client, platform, None)
        method = getattr(endpoint, method_name, None) if endpoint else None
        if not callable(method) or method_name.startswith("_"):
            raise ValueError(f"Unknown RedFox SDK operation: {operation_id}")
        return method(**arguments)
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", help="Optional env file override")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    catalog_parser = sub.add_parser("catalog")
    catalog_parser.add_argument("--out")
    discover_parser = sub.add_parser("discover")
    discover_parser.add_argument("--query", default="")
    discover_parser.add_argument("--platform")
    discover_parser.add_argument("--capability")
    discover_parser.add_argument("--limit", type=int, default=20)
    discover_parser.add_argument("--out")
    call_parser = sub.add_parser("call")
    call_parser.add_argument("--operation", required=True)
    call_parser.add_argument("--args", default="{}")
    call_parser.add_argument("--args-file")
    call_parser.add_argument("--out")
    call_parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    load_env_file(args.env_file)
    try:
        if args.command == "status":
            catalog = build_catalog()
            write_or_print({"has_api_key": has_api_key(), "sdk_version": catalog["sdk_version"], "operation_count": catalog["operation_count"]})
        elif args.command == "catalog":
            write_or_print(build_catalog(), args.out)
        elif args.command == "discover":
            catalog = build_catalog()
            write_or_print(search_catalog(catalog, args.query, args.platform, args.capability, args.limit), args.out)
        elif args.command == "call":
            raw_args = open(args.args_file, encoding="utf-8").read() if args.args_file else args.args
            arguments = json.loads(raw_args)
            if not isinstance(arguments, dict):
                raise ValueError("args must be a JSON object")
            if not args.execute:
                write_or_print({"dry_run": True, "operation": args.operation, "arguments": arguments, "estimated_requests": 1})
            else:
                write_or_print(call_operation(args.operation, arguments), args.out)
        return 0
    except (RuntimeError, ValueError, json.JSONDecodeError, AttributeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
