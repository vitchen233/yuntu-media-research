#!/usr/bin/env python3
"""Store REDFOX_API_KEY in a git-ignored local .env file without echoing it."""

import argparse
import getpass
import os
from pathlib import Path


def write_env(path, api_key):
    if not api_key.strip():
        raise ValueError("API Key cannot be empty")
    path = Path(path)
    path.write_text(f"REDFOX_API_KEY={api_key.strip()}\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=".env", help="Where to save the local env file")
    args = parser.parse_args()
    api_key = getpass.getpass("REDFOX_API_KEY (input hidden): ")
    path = write_env(args.out, api_key)
    print(f"Saved REDFOX_API_KEY to {path}. The key was not printed.")


if __name__ == "__main__":
    main()
