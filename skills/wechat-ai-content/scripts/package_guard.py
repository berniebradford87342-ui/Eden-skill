#!/usr/bin/env python3
"""Offline WeChat package validation, readback comparison and recovery advice.

No network calls, credentials, publishing or remote mutations. Python 3.9+.
"""
import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


class GuardError(ValueError):
    pass


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.images = []
        self.unsafe = []
        self.hidden = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "style", "iframe", "form", "input", "object", "embed", "link"}:
            self.unsafe.append(tag)
        if tag in {"script", "style"}:
            self.hidden += 1
        if any(k.lower().startswith("on") for k in attrs):
            self.unsafe.append("event-handler")
        if tag == "img":
            self.images.append(attrs.get("src") or attrs.get("data-src") or "")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.text.append(data)

    @property
    def visible(self):
        return re.sub(r"\s+", "", "".join(self.text))


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GuardError("Unreadable JSON: " + path.name) from exc


def local_file(root, value):
    if not isinstance(value, str) or not value or urlsplit(value).scheme:
        raise GuardError("Expected a package-relative file")
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise GuardError("File must remain inside the package")
    path = (root / rel).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        raise GuardError("Missing or escaping file: " + value)
    return path


def validate(root):
    manifest = read_json(root / "manifest.json")
    if not isinstance(manifest, dict):
        raise GuardError("Manifest must be an object")
    articles = manifest.get("articles")
    if not isinstance(articles, list) or not articles:
        raise GuardError("Manifest requires a non-empty articles array")
    ids = set()
    hashes = {"manifest.json": hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest()}
    for article in articles:
        if not isinstance(article, dict):
            raise GuardError("Each article must be an object")
        ident = article.get("id")
        if not isinstance(ident, str) or not ident.strip() or ident in ids:
            raise GuardError("Article IDs must be non-empty and unique")
        ids.add(ident)
        if not isinstance(article.get("title"), str) or not article["title"].strip():
            raise GuardError("Missing title: " + ident)
        html = local_file(root, article.get("content_html"))
        cover = local_file(root, article.get("cover_image"))
        page = Page(html.read_text(encoding="utf-8"))
        if page.unsafe or not page.visible:
            raise GuardError("Empty or unsafe HTML: " + ident)
        sources = article.get("source_urls", [])
        if not isinstance(sources, list) or not all(isinstance(u, str) and urlsplit(u).scheme in {"http", "https"} and urlsplit(u).netloc for u in sources):
            raise GuardError("source_urls must contain HTTP(S) URLs")
        for url in sources:
            if url not in "".join(page.text):
                raise GuardError("Source URL is not visible: " + ident)
        for path in [html, cover] + [local_file(root, src) for src in page.images]:
            hashes[path.relative_to(root.resolve()).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ["fact_ledger.md", "humanizer_report.md", "image_plan.md", "review_checklist.md", "skill_usage.json"]:
        path = local_file(root, name)
        if not path.read_text(encoding="utf-8").strip():
            raise GuardError("Empty review artifact: " + name)
    return {"ok": True, "article_count": len(articles), "asset_hashes": hashes,
            "scope": "mechanical_checks_only; editorial and visual reviews still required"}


def image_identity(url):
    if not isinstance(url, str):
        raise GuardError("Missing remote image URL")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise GuardError("Invalid remote image URL")
    if parsed.username or parsed.password or parsed.port or parsed.fragment:
        raise GuardError("Unexpected remote image URL structure")
    if parsed.hostname == "mmbiz.qpic.cn":
        base, _, size = parsed.path.rstrip("/").rpartition("/")
        if size in {"0", "640"} and base:
            return parsed.hostname, base, parsed.query
    # Unknown transformations must match exactly, including scheme.
    return url


def verify(root):
    preflight = validate(root)
    articles = read_json(root / "manifest.json")["articles"]
    result = read_json(root / "upload_result.json")
    remote = read_json(root / "remote_draft.json")
    if result.get("package_hashes") != preflight["asset_hashes"]:
        raise GuardError("Package changed since upload, or upload hashes are missing")
    media_id = result.get("response", {}).get("media_id")
    if not media_id or remote.get("requested_media_id") != media_id:
        raise GuardError("Remote draft identity missing or mismatched")
    news = remote.get("news_item", [])
    log = result.get("upload_log", {})
    covers = log.get("covers", [])
    if len(news) != len(articles) or len(covers) != len(articles):
        raise GuardError("Article or cover count mismatch")
    uploaded = {}
    for item in log.get("inline_images", []):
        path = local_file(root, item.get("local"))
        identity = image_identity(item.get("url"))
        if path in uploaded and uploaded[path] != identity:
            raise GuardError("Conflicting uploaded image mappings")
        uploaded[path] = identity
    checks = []
    for article, actual, cover in zip(articles, news, covers):
        local = Page(local_file(root, article["content_html"]).read_text(encoding="utf-8"))
        remote_page = Page(actual.get("content", ""))
        expected_images = []
        for src in local.images:
            path = local_file(root, src)
            if path not in uploaded:
                raise GuardError("Missing uploaded image mapping: " + src)
            expected_images.append(uploaded[path])
        check = {
            "id": article["id"],
            "title": article["title"] == actual.get("title"),
            "cover": bool(cover.get("media_id")) and cover["media_id"] == actual.get("thumb_media_id") and local_file(root, cover.get("local")) == local_file(root, article["cover_image"]),
            "body": local.visible == remote_page.visible,
            "images": expected_images == [image_identity(src) for src in remote_page.images],
            "sources": all(url in "".join(remote_page.text) for url in article.get("source_urls", [])),
            "safe_html": not remote_page.unsafe,
        }
        check["ok"] = all(value for key, value in check.items() if key != "id")
        checks.append(check)
    return {"ok": all(c["ok"] for c in checks), "media_id": media_id,
            "article_count": preflight["article_count"], "articles": checks,
            "network_operations_executed_by_guard": False}


def resume(root):
    result_path = root / "upload_result.json"
    if result_path.exists():
        result = read_json(result_path)
        media_id = result.get("response", {}).get("media_id")
        if media_id:
            return {"next": "read_back_existing", "media_id": media_id, "may_create": False}
        return {"next": "reconcile_remote_unknown_result", "may_create": False}
    if (root / "upload_attempt.json").exists():
        return {"next": "reconcile_remote_unknown_result", "may_create": False}
    return {"next": "finish_reviews_and_check_remote_duplicates", "may_create": False,
            "reason": "No local attempt does not prove remote absence"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "verify", "resume"])
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    root = args.package.resolve()
    try:
        output = {"validate": validate, "verify": verify, "resume": resume}[args.command](root)
    except (GuardError, KeyError, TypeError, ValueError, OSError) as exc:
        output = {"ok": False, "error": str(exc)}
    if args.command == "verify" and root.is_dir():
        (root / "upload_verification.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
