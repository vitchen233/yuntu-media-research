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


def package_version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def diagnose():
    load_env_file()
    configured_file = next((str(path) for path in env_candidates() if path.is_file()), None)
    sdk_version = package_version("redfox-python-sdk")
    result = {
        "ready": bool(has_api_key() and sdk_version),
        "platform": platform.system(),
        "python": platform.python_version(),
        "python_supported": sys.version_info >= (3, 9),
        "redfox_sdk": sdk_version,
        "redfox_api_key_configured": has_api_key(),
        "config_file_found": configured_file,
        "recommended_config_file": str(default_env_path()),
        "uvx_available": bool(shutil.which("uvx")),
        "git_available": bool(shutil.which("git")),
    }
    result["next_action"] = (
        "ready"
        if result["ready"]
        else "configure-api-key"
        if not result["redfox_api_key_configured"]
        else "install-redfox-sdk"
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
