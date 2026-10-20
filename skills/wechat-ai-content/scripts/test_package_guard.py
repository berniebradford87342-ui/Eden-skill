#!/usr/bin/env python3
"""Offline regression tests: asset loss, corrupt readback and retry ambiguity."""
import json
import tempfile
import unittest
from pathlib import Path
import package_guard as guard


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "assets").mkdir()
        for name in ["cover.jpg", "inline.jpg"]:
            (self.root / "assets" / name).write_bytes(b"offline-fixture")
        self.body = '<p>测试文章。</p><img src="assets/inline.jpg"><p>https://example.org/source</p>'
        (self.root / "main.html").write_text(self.body)
        self.manifest = {"articles": [{"id": "main", "title": "测试标题", "content_html": "main.html", "cover_image": "assets/cover.jpg", "source_urls": ["https://example.org/source"]}]}
        self.save("manifest.json", self.manifest)
        for name in ["fact_ledger.md", "humanizer_report.md", "image_plan.md", "review_checklist.md"]:
            (self.root / name).write_text("Offline fixture; not an actual editorial review.")
        self.save("skill_usage.json", [{"status": "not_run"}])
        self.result = {"response": {"media_id": "draft-fixture"}, "upload_log": {"covers": [{"local": "assets/cover.jpg", "media_id": "cover-fixture"}], "inline_images": [{"local": "assets/inline.jpg", "url": "http://mmbiz.qpic.cn/mmbiz_jpg/same-asset/0?wx_fmt=jpeg"}]}}
        self.remote = {"requested_media_id": "draft-fixture", "news_item": [{"title": "测试标题", "thumb_media_id": "cover-fixture", "content": self.body.replace('src="assets/inline.jpg"', 'data-src="https://mmbiz.qpic.cn/mmbiz_jpg/same-asset/640?wx_fmt=jpeg"')}]}

    def save(self, name, data):
        (self.root / name).write_text(json.dumps(data, ensure_ascii=False))

    def upload_files(self):
        self.result["package_hashes"] = guard.validate(self.root)["asset_hashes"]
        self.save("upload_result.json", self.result)
        self.save("remote_draft.json", self.remote)

    def test_valid_package(self):
        self.assertTrue(guard.validate(self.root)["ok"])

    def test_missing_inline_asset(self):
        (self.root / "assets/inline.jpg").unlink()
        with self.assertRaises(guard.GuardError):
            guard.validate(self.root)

    def test_path_escape_and_symlink(self):
        for path in ["../secret.txt", "/etc/hosts", "https://example.org/cover.jpg"]:
            with self.subTest(path=path), self.assertRaises(guard.GuardError):
                guard.local_file(self.root, path)
        (self.root / "outside").symlink_to("/etc/hosts")
        with self.assertRaises(guard.GuardError):
            guard.local_file(self.root, "outside")

    def test_hyperlink_without_visible_source_fails(self):
        (self.root / "main.html").write_text('<p>测试文章。</p><a href="https://example.org/source">来源</a>')
        with self.assertRaises(guard.GuardError):
            guard.validate(self.root)

    def test_script_or_event_handler_fails(self):
        for extra in ['<script>alert(1)</script>', '<img src="assets/inline.jpg" onerror="alert(1)">']:
            (self.root / "main.html").write_text(self.body + extra)
            with self.assertRaises(guard.GuardError):
                guard.validate(self.root)

    def test_wechat_image_rewrite_is_accepted(self):
        self.upload_files()
        self.assertTrue(guard.verify(self.root)["ok"])

    def test_wrong_asset_with_same_image_count_fails(self):
        self.remote["news_item"][0]["content"] = self.remote["news_item"][0]["content"].replace("same-asset", "different-asset")
        self.upload_files()
        self.assertFalse(guard.verify(self.root)["ok"])

    def test_lost_body_and_source_fails(self):
        self.remote["news_item"][0]["content"] = '<p>测试文章。</p>'
        self.upload_files()
        report = guard.verify(self.root)
        self.assertFalse(report["ok"])
        self.assertFalse(report["articles"][0]["sources"])

    def test_wrong_cover_fails(self):
        self.remote["news_item"][0]["thumb_media_id"] = "other-cover"
        self.upload_files()
        self.assertFalse(guard.verify(self.root)["ok"])

    def test_wrong_draft_identity_fails(self):
        self.remote["requested_media_id"] = "other-draft"
        self.upload_files()
        with self.assertRaises(guard.GuardError):
            guard.verify(self.root)

    def test_image_modified_after_upload_fails(self):
        self.upload_files()
        (self.root / "assets/inline.jpg").write_bytes(b"a new image at the same path")
        with self.assertRaises(guard.GuardError):
            guard.verify(self.root)

    def test_multiple_articles_and_order(self):
        self.manifest["articles"].append(dict(self.manifest["articles"][0], id="sub", title="副文"))
        self.result["upload_log"]["covers"].append(self.result["upload_log"]["covers"][0].copy())
        self.remote["news_item"].append(dict(self.remote["news_item"][0], title="副文"))
        self.save("manifest.json", self.manifest)
        self.upload_files()
        self.assertTrue(guard.verify(self.root)["ok"])
        self.remote["news_item"].reverse()
        self.upload_files()
        self.assertFalse(guard.verify(self.root)["ok"])

    def test_unknown_outcome_never_allows_recreation(self):
        self.save("upload_attempt.json", {"state": "started"})
        self.assertEqual(guard.resume(self.root), {"next": "reconcile_remote_unknown_result", "may_create": False})
        self.save("upload_result.json", {"response": {}})
        self.assertFalse(guard.resume(self.root)["may_create"])
        self.save("upload_result.json", self.result)
        self.assertEqual(guard.resume(self.root)["next"], "read_back_existing")

    def test_no_local_record_requires_remote_duplicate_check(self):
        report = guard.resume(self.root)
        self.assertFalse(report["may_create"])
        self.assertEqual(report["next"], "finish_reviews_and_check_remote_duplicates")


if __name__ == "__main__":
    unittest.main()
