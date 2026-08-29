#!/usr/bin/env python3
"""Check whether a host can run yuntu-media-research without exposing secrets."""

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import sys
from pathlib import Path

from redfox_runtime import default_env_path, env_candidates, has_api_key, load_env_file
from creator_profile import default_profile_path, load_profile, missing_required_fields, profile_is_complete


def package_version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def diagnose():
    load_env_file()
    configured_file = next((str(path) for path in env_candidates() if path.is_file()), None)
    sdk_version = package_version("redfox-python-sdk")
    try:
        profile = load_profile()
        profile_error = None
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        profile = None
        profile_error = str(exc)
    technical_ready = bool(has_api_key() and sdk_version)
    profile_complete = profile_is_complete(profile)
    result = {
        "ready": bool(technical_ready and profile_complete),
        "technical_ready": technical_ready,
        "personalized_research_ready": profile_complete,
        "platform": platform.system(),
        "python": platform.python_version(),
        "python_supported": sys.version_info >= (3, 9),
        "redfox_sdk": sdk_version,
        "redfox_api_key_configured": has_api_key(),
        "config_file_found": configured_file,
        "recommended_config_file": str(default_env_path()),
        "creator_profile_configured": bool(profile),
        "creator_profile_complete": profile_complete,
        "creator_profile_missing_fields": missing_required_fields(profile),
        "creator_profile_file": str(default_profile_path()) if profile else None,
        "recommended_creator_profile_file": str(default_profile_path()),
        "creator_profile_error": profile_error,
        "uvx_available": bool(shutil.which("uvx")),
        "git_available": bool(shutil.which("git")),
    }
    result["next_action"] = (
        "configure-creator-profile"
        if not profile_complete
        else "configure-api-key"
        if not result["redfox_api_key_configured"]
        else "install-redfox-sdk"
        if not sdk_version
        else "ready"
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = diagnose()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("yuntu-media-research doctor")
        for key, value in result.items():
            print(f"- {key}: {value}")
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
