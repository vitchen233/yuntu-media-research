import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "yuntu-media-research"


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


class TestValidation(unittest.TestCase):
    def test_minimum_output_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / "brief.json").write_text("{}\n", encoding="utf-8")
            source = {"source_id": "S001", "url": "https://example.com/post"}
            (root / "source_manifest.jsonl").write_text(json.dumps(source) + "\n", encoding="utf-8")
            (root / "works.jsonl").write_text(json.dumps({"source_id": "S001"}) + "\n", encoding="utf-8")
            (root / "audience_questions.jsonl").write_text(json.dumps({"source_id": "S001"}) + "\n", encoding="utf-8")
            card = {field: "x" for field in validator.TOPIC_FIELDS}
            card.update({"source_ids": ["S001"], "benchmark_urls": ["https://example.com/post"]})
            (root / "topic_cards.jsonl").write_text(json.dumps(card) + "\n", encoding="utf-8")
            self.assertEqual(validator.validate(root), [])


if __name__ == "__main__":
    unittest.main()
