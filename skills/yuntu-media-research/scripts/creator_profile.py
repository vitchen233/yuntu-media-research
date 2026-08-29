#!/usr/bin/env python3
"""Load and validate the local creator research profile."""

import json
import os
from pathlib import Path

from redfox_runtime import user_config_dir


REQUIRED_FIELDS = ("creator_niche", "target_audience", "platforms")


def default_profile_path():
    configured = os.getenv("YUNTU_MEDIA_RESEARCH_PROFILE")
    return Path(configured).expanduser() if configured else user_config_dir() / "creator-profile.json"


def load_profile(path=None):
    profile_path = Path(path).expanduser() if path else default_profile_path()
    if not profile_path.is_file():
        return None
    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Creator profile must be a JSON object")
    return payload


def missing_required_fields(profile):
    profile = profile or {}
    missing = []
    for field in REQUIRED_FIELDS:
        value = profile.get(field)
        if value is None or value == "" or value == []:
            missing.append(field)
    return missing


def profile_is_complete(profile):
    return bool(profile) and not missing_required_fields(profile)


def merge_profile(profile, task):
    """Merge persistent defaults with explicit task values without mutating either."""
    merged = dict(profile or {})
    for key, value in (task or {}).items():
        if value is not None and value != "" and value != []:
            merged[key] = value
    return merged
