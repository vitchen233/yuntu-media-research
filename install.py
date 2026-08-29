#!/usr/bin/env python3
"""Install the bundled skill into a supported Agent skill directory."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


HOST_PATHS = {
    "codex": Path.home() / ".codex" / "skills",
    "claude": Path.home() / ".claude" / "skills",
    "workbuddy": Path.home() / ".workbuddy" / "skills",
    "workbuddy-ai": Path.home() / ".workbuddy-ai" / "skills",
    "agents": Path.home() / ".agents" / "skills",
}


def install(source, target_root, force=False):
    target = target_root / "yuntu-media-research"
    if target.exists() or target.is_symlink():
        if not force:
            raise FileExistsError(f"Target already exists: {target}. Re-run with --force to replace it.")
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()
    target_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    return target


def main():
    parser = argparse.ArgumentParser(description="Install yuntu-media-research for one Agent host")
    parser.add_argument("--host", choices=sorted(HOST_PATHS), help="Target Agent host")
    parser.add_argument("--target", help="Custom skills directory for another SKILL.md-compatible host")
    parser.add_argument("--force", action="store_true", help="Replace an existing installation")
    parser.add_argument("--with-deps", action="store_true", help="Install the RedFox Python SDK")
    args = parser.parse_args()
    if bool(args.host) == bool(args.target):
        parser.error("choose exactly one of --host or --target")
    root = Path(__file__).resolve().parent
    source = root / "skills" / "yuntu-media-research"
    target_root = HOST_PATHS[args.host] if args.host else Path(args.target).expanduser()
    if args.with_deps:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(root / "requirements.txt")], check=True)
    target = install(source, target_root, args.force)
    print(f"Installed yuntu-media-research to {target}")
    print("Restart or reload your Agent, then say: 第一次使用 yuntu-media-research，请帮我完成配置检查。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
