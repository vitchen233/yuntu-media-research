import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import date
from unittest import mock

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
configure_profile = load_script("configure_profile.py")
creator_profile = load_script("creator_profile.py")
ranking = load_script("rank_topics.py")
validator = load_script("validate_output.py")
renderer = load_script("render_report.py")
report_validator = load_script("validate_report.py")
normalizer = load_script("normalize.py")
redfox_catalog = load_script("redfox_catalog.py")
redfox_mcp = load_script("redfox_mcp.py")
estimate_cost = load_script("estimate_cost.py")
doctor = load_script("doctor.py")
draft_validator = load_script("validate_draft.py")

INSTALL_SPEC = importlib.util.spec_from_file_location("installer", ROOT / "install.py")
installer = importlib.util.module_from_spec(INSTALL_SPEC)
INSTALL_SPEC.loader.exec_module(installer)


class TestCollector(unittest.TestCase):
    def test_plan_counts_requests(self):
        self.assertEqual(collector.plan({"queries": ["a", "b"], "pages_per_query": 2})["estimated_requests"], 4)

    def test_relative_three_day_window(self):
        self.assertEqual(collector.resolve_time_window({"days": 3}, date(2026, 8, 30)), ("2026-08-28", "2026-08-30"))

    def test_explicit_dates_override_relative_window(self):
        config = {"days": 3, "start_date": "2026-08-01", "end_date": "2026-08-07"}
        self.assertEqual(collector.resolve_time_window(config, date(2026, 8, 30)), ("2026-08-01", "2026-08-07"))

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

    def test_user_config_env_file_is_discovered(self):
        runtime = load_script("redfox_runtime.py")
        with tempfile.TemporaryDirectory() as temp:
            config_root = pathlib.Path(temp) / "config"
            env_file = config_root / "yuntu-media-research" / ".env"
            env_file.parent.mkdir(parents=True)
            env_file.write_text("REDFOX_API_KEY=test-user-config\n", encoding="utf-8")
            old = runtime.os.environ.pop("REDFOX_API_KEY", None)
            try:
                with mock.patch.dict(runtime.os.environ, {"XDG_CONFIG_HOME": str(config_root)}, clear=False), mock.patch.object(runtime.Path, "cwd", return_value=pathlib.Path(temp) / "workspace"):
                    self.assertTrue(runtime.load_env_file())
                    self.assertEqual(runtime.os.environ["REDFOX_API_KEY"], "test-user-config")
            finally:
                runtime.os.environ.pop("REDFOX_API_KEY", None)
                if old is not None:
                    runtime.os.environ["REDFOX_API_KEY"] = old

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


class TestHtmlRenderer(unittest.TestCase):
    def test_topic_report_is_standalone_and_escaped(self):
        data = {
            "report_type": "topic-research",
            "title": "A < B",
            "sources": [],
            "candidates": [],
            "limitations": [],
        }
        page = renderer.render(data)
        self.assertIn("<!doctype html>", page.lower())
        self.assertIn("A &lt; B", page)
        self.assertNotIn("https://fonts", page)

    def test_all_report_types_render(self):
        for report_type in renderer.ACCENTS:
            page = renderer.render({"report_type": report_type, "title": report_type})
            self.assertIn("YUNTU MEDIA RESEARCH", page)

    def test_creator_report_renders_rich_analysis(self):
        data = {
            "report_type": "creator-analysis",
            "title": "creator",
            "profile": {"positioning": "AI实战"},
            "hook_patterns": [{"label": "结果钩子", "share": 50, "examples": ["结果"], "mechanism": "前置收益"}],
            "method_matrix": [{"stage": "开头", "action": "展示", "proof": "录屏", "purpose": "停留"}],
            "conversion_funnel": [{"stage": "01", "label": "停留", "detail": "看到结果", "width": 100}],
            "engagement_scatter": [{"title": "A", "likes": 100, "save_rate": 0.5, "share_rate": 0.1, "url": "https://example.com"}],
        }
        page = renderer.render(data)
        self.assertIn("钩子系统", page)
        self.assertIn("内容方法", page)
        self.assertIn("转化路径", page)

    def test_topic_report_renders_research_dashboard(self):
        data = {"report_type": "topic-research", "title": "topic", "signal_map": [{"label": "Skill", "share": 40}], "evidence_ladder": [{"label": "实时搜索"}], "candidates": []}
        page = renderer.render(data)
        self.assertIn("观众正在用什么方式找答案", page)
        self.assertIn("证据链", page)

    def test_structure_report_renders_visual_analysis(self):
        data = {"report_type": "content-structure-analysis", "title": "structure", "attention_curve": [{"time": "00:00", "label": "钩子", "strength": 90}], "visual_mix": [{"label": "录屏", "share": 60}], "stages": []}
        page = renderer.render(data)
        self.assertIn("注意力曲线", page)
        self.assertIn("画面组成", page)

    def test_report_validator_rejects_placeholder_and_missing_sources(self):
        data = {"report_type": "topic-research", "title": "TODO", "summary": "x", "generated_at": "now", "method": "x", "limitations": ["x"], "candidates": [{}, {}, {}]}
        errors = report_validator.validate(data)
        self.assertTrue(any("placeholder" in error for error in errors))
        self.assertTrue(any("source" in error for error in errors))

    def test_wide_row_normalization(self):
        row = {"videoId": "42", "opusUrl": "https://example.org/video/42", "content": "x", "authorName": "a", "likeCount": 9}
        result = collector.normalize_row(row, "wide")
        self.assertEqual(result["work_id"], "42")
        self.assertEqual(result["likes"], 9)


class TestDistribution(unittest.TestCase):
    def test_custom_host_install_copies_complete_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            target = installer.install(ROOT / "skills" / "yuntu-media-research", pathlib.Path(temp))
            self.assertTrue((target / "SKILL.md").is_file())
            self.assertTrue((target / "references" / "prompt-library.md").is_file())
            self.assertTrue((target / "scripts" / "doctor.py").is_file())

    def test_installer_refuses_implicit_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            installer.install(ROOT / "skills" / "yuntu-media-research", root)
            with self.assertRaises(FileExistsError):
                installer.install(ROOT / "skills" / "yuntu-media-research", root)

    def test_doctor_never_returns_key_value(self):
        secret = "secret-value-that-must-not-leak"
        with mock.patch.dict(doctor.os.environ, {"REDFOX_API_KEY": secret}, clear=False):
            result = doctor.diagnose()
        self.assertTrue(result["redfox_api_key_configured"])
        self.assertNotIn(secret, json.dumps(result))

    def test_creator_profile_round_trip_and_task_override(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "creator-profile.json"
            profile = configure_profile.write_profile(path, {
                "creator_niche": "AI自媒体",
                "target_audience": "个人创作者",
                "platforms": ["抖音"],
                "content_goals": ["涨粉"],
            })
            loaded = creator_profile.load_profile(profile)
            merged = creator_profile.merge_profile(loaded, {"target_audience": "刚开始学AI的创作者"})
            self.assertTrue(creator_profile.profile_is_complete(loaded))
            self.assertEqual(merged["creator_niche"], "AI自媒体")
            self.assertEqual(merged["target_audience"], "刚开始学AI的创作者")

    def test_doctor_routes_to_creator_profile_after_technical_setup(self):
        with mock.patch.object(doctor, "has_api_key", return_value=True), mock.patch.object(doctor, "package_version", return_value="0.3.0"), mock.patch.object(doctor, "load_profile", return_value=None):
            result = doctor.diagnose()
        self.assertTrue(result["technical_ready"])
        self.assertFalse(result["ready"])
        self.assertEqual(result["next_action"], "configure-creator-profile")


class TestDraftValidation(unittest.TestCase):
    def test_valid_grounded_draft_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            for name in ("selected_topic.md", "draft.md", "audit.md"):
                (root / name).write_text("真实内容\n", encoding="utf-8")
            source_map = {"claims": [{"claim": "近期出现相关作品", "basis": ["S001"]}]}
            (root / "draft_source_map.json").write_text(json.dumps(source_map), encoding="utf-8")
            self.assertEqual(draft_validator.validate(root), [])

    def test_draft_bundle_rejects_placeholder_and_empty_map(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            for name in ("selected_topic.md", "audit.md"):
                (root / name).write_text("真实内容\n", encoding="utf-8")
            (root / "draft.md").write_text("TODO\n", encoding="utf-8")
            (root / "draft_source_map.json").write_text('{"claims": []}', encoding="utf-8")
            errors = draft_validator.validate(root)
            self.assertTrue(any("placeholder" in error for error in errors))
            self.assertTrue(any("no claims" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
