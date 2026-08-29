#!/usr/bin/env python3
"""Create or update the user-level creator research profile."""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from creator_profile import default_profile_path, load_profile, missing_required_fields


def split_list(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value or "").replace("，", ",").split(",") if item.strip()]


def normalize_profile(profile):
    result = dict(profile)
    result["schema_version"] = 1
    for field in (
        "platforms",
        "audience_problems",
        "content_goals",
        "preferred_tools",
        "delivery_assets",
        "content_boundaries",
    ):
        result[field] = split_list(result.get(field, []))
    result["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    missing = missing_required_fields(result)
    if missing:
        raise ValueError("Missing required profile fields: " + ", ".join(missing))
    return result


def write_profile(path, profile):
    output = Path(path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(normalize_profile(profile), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(output, 0o600)
    except OSError:
        pass
    return output


def ask(label, current="", required=False):
    suffix = f" [{current}]" if current else ""
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if current:
            return current
        if not required:
            return ""
        print("此项用于个性化研究，不能为空。")


def interactive_profile(existing=None):
    existing = existing or {}
    return {
        "creator_name": ask("你希望报告怎样称呼你", existing.get("creator_name", "")),
        "creator_role": ask("你的身份或内容背景", existing.get("creator_role", "")),
        "creator_niche": ask("你的主要赛道", existing.get("creator_niche", ""), required=True),
        "platforms": ask("主要发布平台，多个用逗号分隔", ", ".join(existing.get("platforms", [])), required=True),
        "target_audience": ask("你的核心目标受众", existing.get("target_audience", ""), required=True),
        "audience_problems": ask("受众反复遇到的问题，多个用逗号分隔", ", ".join(existing.get("audience_problems", []))),
        "content_goals": ask("当前内容目标，多个用逗号分隔", ", ".join(existing.get("content_goals", []))),
        "preferred_tools": ask("优先讲或使用的工具，多个用逗号分隔", ", ".join(existing.get("preferred_tools", []))),
        "delivery_assets": ask("常用交付物，多个用逗号分隔", ", ".join(existing.get("delivery_assets", []))),
        "content_boundaries": ask("不想讲或不能承诺的内容，多个用逗号分隔", ", ".join(existing.get("content_boundaries", []))),
        "notes": ask("其他长期说明", existing.get("notes", "")),
    }


def main():
    parser = argparse.ArgumentParser(description="Configure the creator research profile")
    parser.add_argument("--input", help="Import a prepared JSON profile")
    parser.add_argument("--out", help="Override the user-level profile path")
    parser.add_argument("--show-path", action="store_true", help="Print the profile path and exit")
    args = parser.parse_args()
    output = Path(args.out).expanduser() if args.out else default_profile_path()
    if args.show_path:
        print(output)
        return 0
    if args.input:
        profile = json.loads(Path(args.input).read_text(encoding="utf-8"))
    else:
        profile = interactive_profile(load_profile(output))
    path = write_profile(output, profile)
    print(f"Saved creator research profile to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
