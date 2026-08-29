#!/usr/bin/env python3
"""Normalize RedFox platform records into auditable cross-platform schemas."""

import argparse
import json
from pathlib import Path


SCHEMAS = {
    "work": ["platform", "work_id", "url", "author_id", "author_name", "title", "text", "published_at", "views", "likes", "comments", "shares", "saves", "followers", "duration_sec", "raw_source"],
    "account": ["platform", "account_id", "account_name", "url", "bio", "followers", "following", "works", "likes", "raw_source"],
    "comment": ["platform", "comment_id", "work_id", "text", "likes", "replies", "published_at", "raw_source"],
}

ALIASES = {
    "work_id": ["work_id", "workId", "photoId", "video_id", "videoId", "aweme_id", "opus_id", "bvid", "id"],
    "url": ["url", "workUrl", "share_url", "web_url", "link"],
    "author_id": ["author_id", "authorId", "user_id", "userId", "account_id", "accountId", "mid", "sec_uid"],
    "author_name": ["author_name", "authorName", "accountName", "userName", "nickname", "name"],
    "title": ["title", "desc", "name"],
    "text": ["text", "content", "desc", "title"],
    "published_at": ["published_at", "publishTime", "create_time", "createTime", "gmtCreate", "pubdate"],
    "views": ["views", "viewCount", "playCount", "play_count", "readCount"],
    "likes": ["likes", "likeCount", "digg_count", "diggCount", "liked_count"],
    "comments": ["comments", "commentCount", "comment_count"],
    "shares": ["shares", "shareCount", "share_count", "forwardCount"],
    "saves": ["saves", "collectCount", "collect_count", "favoriteCount"],
    "followers": ["followers", "followerCount", "fans", "fansCount"],
    "duration_sec": ["duration_sec", "duration", "videoDuration"],
    "account_id": ["account_id", "accountId", "user_id", "userId", "uid", "mid", "sec_uid", "id"],
    "account_name": ["account_name", "accountName", "userName", "nickname", "name"],
    "bio": ["bio", "signature", "description", "desc"],
    "following": ["following", "followingCount", "follow_count"],
    "works": ["works", "workCount", "aweme_count", "videoCount"],
    "comment_id": ["comment_id", "commentId", "cid", "id"],
    "replies": ["replies", "replyCount", "reply_count"],
}


def nested_values(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from nested_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_values(child)


def find_value(row, aliases):
    alias_set = set(aliases)
    for key, value in nested_values(row):
        if key in alias_set and not isinstance(value, (dict, list)) and value is not None:
            return value, key
    return None, None


def normalize_record(row, kind, platform, raw_source=None):
    if kind not in SCHEMAS:
        raise ValueError(f"unsupported kind: {kind}")
    result = {"platform": platform}
    observed = {}
    for field in SCHEMAS[kind]:
        if field == "platform":
            continue
        if field == "raw_source":
            result[field] = raw_source
            continue
        value, source_field = find_value(row, ALIASES.get(field, [field]))
        result[field] = value
        if source_field:
            observed[field] = source_field
    derived = {}
    if kind == "work" and platform == "douyin" and not result.get("url") and result.get("work_id"):
        result["url"] = f"https://www.douyin.com/video/{result['work_id']}"
        derived["url"] = "calculated-from-work-id"
    result["normalization"] = {
        "observed_field_map": observed,
        "derived_fields": derived,
        "missing_fields": [field for field in SCHEMAS[kind] if result.get(field) is None],
    }
    return result


def rows_from_payload(payload, list_path=None):
    current = payload
    if isinstance(current, dict) and isinstance(current.get("structuredContent"), dict):
        current = current["structuredContent"]
    elif isinstance(current, dict) and isinstance(current.get("content"), list):
        for block in current["content"]:
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                try:
                    current = json.loads(block["text"])
                    break
                except json.JSONDecodeError:
                    continue
    if list_path:
        for part in list_path.split("."):
            current = current[int(part)] if isinstance(current, list) else current.get(part)
    if isinstance(current, list):
        return current
    if isinstance(current, dict):
        for key in ("list", "items", "data", "records", "comments"):
            if isinstance(current.get(key), list):
                return current[key]
        return [current]
    raise ValueError("payload does not contain records")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--kind", choices=sorted(SCHEMAS), required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--list-path")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    input_path = Path(args.input)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    rows = rows_from_payload(payload, args.list_path)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(normalize_record(row, args.kind, args.platform, str(input_path)), ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(f"wrote {len(rows)} normalized {args.kind} records -> {output}")


if __name__ == "__main__":
    main()
