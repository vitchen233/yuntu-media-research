#!/usr/bin/env python3
"""Plan and collect RedFox Douyin search results without exposing credentials."""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def load_env_file(path):
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


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("platform") != "douyin":
        raise ValueError("v1.0 currently supports platform=douyin only")
    if not config.get("queries"):
        raise ValueError("queries must not be empty")
    return config


def plan(config):
    pages = int(config.get("pages_per_query", 1))
    if pages < 1 or pages > 5:
        raise ValueError("pages_per_query must be between 1 and 5")
    requests = len(config["queries"]) * pages
    return {"search_mode": config.get("search_mode", "quality"), "queries": len(config["queries"]), "pages_per_query": pages, "estimated_requests": requests, "price_note": "Check current RedFox pricing before execution."}


def matches_relevance(work, required_any_groups):
    if not required_any_groups:
        return True, []
    text = f"{work.get('title') or ''} {work.get('content') or ''}".lower()
    missing_groups = []
    for group in required_any_groups:
        if not any(str(term).lower() in text for term in group):
            missing_groups.append(group)
    return not missing_groups, missing_groups


def filter_pairs(manifest, works, required_any_groups):
    manifest_by_source = {row["source_id"]: row for row in manifest}
    relevant_manifest = []
    relevant_works = []
    exclusions = []
    for work in works:
        keep, missing_groups = matches_relevance(work, required_any_groups)
        if keep:
            relevant_works.append(work)
            relevant_manifest.append(manifest_by_source[work["source_id"]])
        else:
            exclusions.append({
                "source_id": work["source_id"],
                "url": work.get("url"),
                "title": work.get("title"),
                "reason": "missing-required-keyword-group",
                "missing_groups": missing_groups,
            })
    return relevant_manifest, relevant_works, exclusions


def normalize_row(row, search_mode):
    if search_mode == "ai":
        work_id = str(row.get("photoId") or "")
        observed_url = row.get("url") or ""
        calculated_url = f"https://www.douyin.com/video/{work_id}" if work_id else ""
        return {
            "work_id": work_id,
            "url": observed_url or calculated_url,
            "url_basis": "observed" if observed_url else "calculated-from-photo-id",
            "title": row.get("title") or "",
            "content": row.get("title") or "",
            "author": row.get("userName") or "",
            "author_url": None,
            "published_at": row.get("gmtCreate"),
            "likes": row.get("likeCount"),
            "comments": row.get("commentCount"),
            "shares": row.get("shareCount"),
            "saves": None,
            "followers": None,
            "comment_top_keywords": None,
            "crawl_time": row.get("gmtModified"),
        }
    return {
        "work_id": str(row.get("workId") or ""),
        "url": row.get("workUrl") or "",
        "url_basis": "observed",
        "title": row.get("title") or "",
        "content": row.get("content") or "",
        "author": row.get("accountName") or "",
        "author_url": row.get("authorLink"),
        "published_at": row.get("publishTime"),
        "likes": row.get("likeCount"),
        "comments": row.get("commentCount"),
        "shares": row.get("shareCount"),
        "saves": row.get("collectCount"),
        "followers": row.get("followerCount"),
        "comment_top_keywords": row.get("commentTopKeywords"),
        "crawl_time": row.get("crawlTime"),
    }


def import_client():
    try:
        from redfox import RedFoxClient
    except ImportError as exc:
        raise RuntimeError("Install optional dependency: pip install redfox-python-sdk") from exc
    return RedFoxClient


def collect(config, out_root):
    if not os.getenv("REDFOX_API_KEY", "").strip():
        raise RuntimeError("REDFOX_API_KEY is not configured")
    RedFoxClient = import_client()
    client = RedFoxClient()
    out_root = Path(out_root)
    raw_root = out_root / "raw" / "redfox"
    raw_root.mkdir(parents=True, exist_ok=True)
    collected_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    manifest = []
    works = []
    seen = set()
    sequence = 1
    pages = int(config.get("pages_per_query", 1))
    search_mode = config.get("search_mode", "quality")
    if search_mode not in {"quality", "ai"}:
        raise ValueError("search_mode must be quality or ai")

    for query_index, query in enumerate(config["queries"], 1):
        for page in range(pages):
            offset = page * 20
            if search_mode == "ai":
                start_time = f"{config.get('start_date')} 00:00:00" if config.get("start_date") else None
                end_time = f"{config.get('end_date')} 23:59:59" if config.get("end_date") else None
                result = client.douyin.search_ai_articles(keyword=query, page_num=page + 1, page_size=20, start_time=start_time, end_time=end_time)
            else:
                payload = {
                    "keyword": query,
                    "startDate": config.get("start_date"),
                    "endDate": config.get("end_date"),
                    "offset": offset,
                    "sortType": config.get("sort_type", "_0"),
                }
                result = client.post("/story/api/dyData/searchArticle", data=payload)
            raw_path = raw_root / f"{search_mode}-search-{query_index:02d}-{page + 1:02d}.json"
            raw_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            for row in result.get("list", []):
                normalized = normalize_row(row, search_mode)
                work_id = normalized["work_id"]
                url = normalized["url"]
                dedupe_key = work_id or url
                if not dedupe_key or dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                source_id = f"S{sequence:03d}"
                sequence += 1
                observed = [key for key, value in row.items() if value is not None]
                manifest.append({
                    "source_id": source_id,
                    "url": url,
                    "source_type": f"redfox-douyin-{search_mode}-work",
                    "platform": "douyin",
                    "title": normalized["title"],
                    "author": normalized["author"],
                    "published_at": normalized["published_at"],
                    "collected_at": collected_at,
                    "access_status": "ok",
                    "observed_fields": observed,
                    "url_basis": normalized["url_basis"],
                    "query": query,
                    "raw_source": str(raw_path.relative_to(out_root)),
                })
                works.append({"source_id": source_id, "platform": "douyin", **normalized})

    relevant_manifest, relevant_works, exclusions = filter_pairs(manifest, works, config.get("required_any_groups", []))
    outputs = (
        ("source_manifest_collected.jsonl", manifest),
        ("works_collected.jsonl", works),
        ("source_manifest.jsonl", relevant_manifest),
        ("works.jsonl", relevant_works),
        ("relevance_exclusions.jsonl", exclusions),
    )
    for filename, rows in outputs:
        (out_root / filename).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return {"collected": len(works), "relevant": len(relevant_works), "excluded": len(exclusions), "raw_files": len(config["queries"]) * pages}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env", help="Local env file; defaults to .env in the current directory")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("--config", required=True)
    collect_parser = sub.add_parser("collect")
    collect_parser.add_argument("--config", required=True)
    collect_parser.add_argument("--out", required=True)
    collect_parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    load_env_file(args.env_file)

    if args.command == "status":
        print(json.dumps({"has_redfox_api_key": bool(os.getenv("REDFOX_API_KEY", "").strip())}))
        return
    config = load_config(args.config)
    request_plan = plan(config)
    if args.command == "plan" or not args.execute:
        print(json.dumps(request_plan, ensure_ascii=False, indent=2))
        return
    print(json.dumps({"plan": request_plan, "result": collect(config, args.out)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
