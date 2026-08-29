import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "yuntu-media-research"
sys.path.insert(0, str(SKILL / "scripts"))


def load_script(name):
    path = SKILL / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


collector = load_script("redfox_collect.py")
configure_key = load_script("configure_key.py")
ranking = load_script("rank_topics.py")
validator = load_script("validate_output.py")
normalizer = load_script("normalize.py")
redfox_catalog = load_script("redfox_catalog.py")
redfox_mcp = load_script("redfox_mcp.py")
estimate_cost = load_script("estimate_cost.py")


class TestCollector(unittest.TestCase):
    def test_plan_counts_requests(self):
        self.assertEqual(collector.plan({"queries": ["a", "b"], "pages_per_query": 2})["estimated_requests"], 4)

    def test_local_env_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / ".env"
            configure_key.write_env(path, "test-key-value")
            old = collector.os.environ.pop("REDFOX_API_KEY", None)
            try:
                self.assertTrue(collector.load_env_file(path))
                self.assertEqual(collector.os.environ["REDFOX_API_KEY"], "test-key-value")
            finally:
                collector.os.environ.pop("REDFOX_API_KEY", None)
                if old is not None:
                    collector.os.environ["REDFOX_API_KEY"] = old

    def test_relevance_requires_each_group(self):
        groups = [["AI", "Codex"], ["自媒体", "选题"]]
        keep, _ = collector.matches_relevance({"title": "用Codex给自媒体找选题", "content": ""}, groups)
        reject, missing = collector.matches_relevance({"title": "AI新闻", "content": ""}, groups)
        self.assertTrue(keep)
        self.assertFalse(reject)
        self.assertEqual(missing, [["自媒体", "选题"]])

    def test_ai_row_records_calculated_url(self):
        row = collector.normalize_row({"photoId": "123", "title": "Codex教程", "userName": "A"}, "ai")
        self.assertEqual(row["url"], "https://www.douyin.com/video/123")
        self.assertEqual(row["url_basis"], "calculated-from-photo-id")


class TestRanking(unittest.TestCase):
    def test_sources_avoid_penalty(self):
        base = {field: 4 for field in ranking.FIELDS}
        self.assertGreater(ranking.score(dict(base, source_ids=["S001"])), ranking.score(dict(base, source_ids=[])))


class TestRedFoxCatalog(unittest.TestCase):
    def test_catalog_discovers_sdk_operations(self):
        catalog = redfox_catalog.build_catalog()
        ids = {item["operation_id"] for item in catalog["operations"]}
        self.assertIn("sdk.douyin.search_articles", ids)
        self.assertIn("sdk.xiaohongshu.comment_submit", ids)
        self.assertGreater(catalog["operation_count"], 20)

    def test_catalog_extracts_price_class(self):
        catalog = redfox_catalog.build_catalog()
        by_id = {item["operation_id"]: item for item in catalog["operations"]}
        self.assertEqual(by_id["sdk.douyin.search_articles"]["price_class"], "quality")
        self.assertEqual(by_id["sdk.toutiao.search_works"]["price_class"], "realtime")

    def test_catalog_search_filters_platform_and_capability(self):
        catalog = redfox_catalog.build_catalog()
        hits = redfox_catalog.search_catalog(catalog, "search", platform="bilibili", capability="search")
        self.assertTrue(hits)
        self.assertTrue(all(item["platform"] == "bilibili" for item in hits))


class TestRedFoxMcp(unittest.TestCase):
    def test_tool_search(self):
        tools = [
            {"name": "douyin_search_works", "description": "search works"},
            {"name": "xiaohongshu_search_works", "description": "search notes"},
        ]
        hits = redfox_mcp.tool_search(tools, "search", platform="douyin")
        self.assertEqual([item["name"] for item in hits], ["douyin_search_works"])

    def test_tool_annotation_extracts_price_class(self):
        tool = redfox_mcp.annotate_tool({"name": "x", "description": "搜索作品（优质库）"})
        self.assertEqual(tool["yuntu"]["price_class"], "quality")

    def test_command_has_launcher_and_package(self):
        parts = redfox_mcp.command_parts()
        self.assertTrue(parts[0].endswith(("uvx", "uvx.exe")))
        self.assertEqual(parts[1], "redfox-mcp")


class TestCost(unittest.TestCase):
    def test_quality_and_realtime_estimate(self):
        result = estimate_cost.estimate_items([
            {"operation": "a", "requests": 2, "price_class": "quality"},
            {"operation": "b", "requests": 1, "price_class": "realtime"},
        ])
        self.assertEqual(result["priced_requests"], 3)
        self.assertAlmostEqual(result["estimated_cost_cny"], 0.14)

    def test_unknown_price_is_not_guessed(self):
        result = estimate_cost.estimate_items([{"operation": "x", "requests": 1, "price_class": "unknown"}])
        self.assertEqual(result["estimated_cost_cny"], 0)
        self.assertEqual(result["estimated_total_range_cny"], [0.02, 0.06])
        self.assertEqual(result["unknown_price_operations"], ["x"])


class TestNormalization(unittest.TestCase):
    def test_nested_douyin_work(self):
        row = {"photoId": "1", "author": {"nickname": "云途"}, "stats": {"likeCount": 8}}
        result = normalizer.normalize_record(row, "work", "douyin", "raw.json")
        self.assertEqual(result["work_id"], "1")
        self.assertEqual(result["url"], "https://www.douyin.com/video/1")
        self.assertEqual(result["normalization"]["derived_fields"]["url"], "calculated-from-work-id")
        self.assertEqual(result["author_name"], "云途")
        self.assertEqual(result["likes"], 8)
        self.assertIn("views", result["normalization"]["missing_fields"])

    def test_mcp_structured_content_is_unwrapped(self):
        payload = {"structuredContent": {"list": [{"photoId": "2"}]}}
        self.assertEqual(normalizer.rows_from_payload(payload)[0]["photoId"], "2")


class TestValidation(unittest.TestCase):
    def test_minimum_output_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / "brief.json").write_text("{}\n", encoding="utf-8")
            source = {"source_id": "S001", "url": "https://example.com/post"}
            (root / "source_manifest.jsonl").write_text(json.dumps(source) + "\n", encoding="utf-8")
            (root / "works.jsonl").write_text(json.dumps({"source_id": "S001"}) + "\n", encoding="utf-8")
            card = {field: "x" for field in validator.TOPIC_FIELDS}
            card.update({"source_ids": ["S001"], "benchmark_urls": ["https://example.com/post"]})
            (root / "topic_cards.jsonl").write_text(json.dumps(card) + "\n", encoding="utf-8")
            self.assertEqual(validator.validate(root), [])


if __name__ == "__main__":
    unittest.main()
