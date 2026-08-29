#!/usr/bin/env python3
"""Shared local runtime helpers for RedFox scripts."""

import json
import os
from pathlib import Path


def load_env_file(path=".env"):
    path = Path(path)
    if not path.is_file():
        return False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() != "REDFOX_API_KEY":
            continue
        value = value.strip().strip('"').strip("'")
        if value and not os.getenv("REDFOX_API_KEY"):
            os.environ["REDFOX_API_KEY"] = value
        return bool(value)
    return False


def has_api_key():
    return bool(os.getenv("REDFOX_API_KEY", "").strip())


def write_or_print(payload, out=None):
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if out:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
        return str(path)
    print(text)
    return None
