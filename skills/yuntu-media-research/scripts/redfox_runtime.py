#!/usr/bin/env python3
"""Shared local runtime helpers for RedFox scripts."""

import json
import os
from pathlib import Path


def user_config_dir():
    if os.name == "nt":
        root = Path(os.getenv("APPDATA") or (Path.home() / "AppData" / "Roaming"))
    else:
        root = Path(os.getenv("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return root / "yuntu-media-research"


def default_env_path():
    return user_config_dir() / ".env"


def env_candidates(path=None):
    candidates = []
    if path:
        candidates.append(Path(path).expanduser())
    configured = os.getenv("YUNTU_MEDIA_RESEARCH_ENV")
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend((Path.cwd() / ".env", default_env_path()))
    unique = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in unique:
            unique.append(resolved)
    return unique


def load_env_file(path=None):
    for candidate in env_candidates(path):
        if candidate.is_file() and _load_env_candidate(candidate):
            return True
    return False


def _load_env_candidate(path):
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
