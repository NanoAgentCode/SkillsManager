import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = Path("skills/content-operations/wechat-format")


class WechatToolsTests(unittest.TestCase):
    def test_dry_run_checks_local_files_without_requests_or_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cli = root / "scripts" / "wechat-tools.py"
            cli.parent.mkdir()
            shutil.copy2(ROOT / "scripts" / cli.name, cli)
            scripts = root / SKILL / "scripts"
            scripts.mkdir(parents=True)
            for name in ("publish.py", "config_loader.py"):
                shutil.copy2(ROOT / SKILL / "scripts" / name, scripts / name)
            (root / "requests.py").write_text("raise ModuleNotFoundError('requests')\n", encoding="utf-8")
            env = {**os.environ, "PYTHONPATH": str(root)}
            article = root / "article.html"
            article.write_text(
                '<h1>Offline title</h1><img src="body.png"><img src="https://example.invalid/remote.png">',
                encoding="utf-8",
            )
            body = root / "body.png"
            body.write_bytes(b"body")
            cover = root / "cover.jpg"
            cover.write_bytes(b"cover")
            args = ("draft", "--dir", root, "--cover", cover, "--dry-run")
            preview = self.run_cli(cli, *args, env=env)
            self.assertIn("Offline title", preview.stdout)
            self.assertIn("cover.jpg", preview.stdout)
            self.assertIn("外链图片: 1", preview.stdout)

            body.unlink()
            self.assertIn("body.png", self.run_cli(cli, *args, env=env, status=1).stderr)
            body.write_bytes(b"body")
            (root / "images").mkdir()
            cover.rename(root / "images/cover.jpg")
            self.run_cli(cli, "draft", "--dir", root, "--dry-run", env=env)
            self.assertIn("封面", self.run_cli(cli, *args, env=env, status=1).stderr)
            cover.write_bytes(b"cover")
            article.write_text("  ", encoding="utf-8")
            self.assertIn("正文", self.run_cli(cli, *args, env=env, status=1).stderr)

    @unittest.skipUnless(importlib.util.find_spec("markdown"), "Install markdown to test the renderer")
    def test_render_and_submit_draft_using_mock_http(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cli = root / "scripts" / "wechat-tools.py"
            cli.parent.mkdir()
            shutil.copy2(ROOT / "scripts" / cli.name, cli)
            target = root / SKILL
            for folder in ("scripts", "templates", "themes"):
                shutil.copytree(ROOT / SKILL / folder, target / folder)

            source = root / "article.md"
            (root / "body.png").write_bytes(b"body image")
            source.write_text("# Sample article\n\nSample body.\n\n![Body](body.png)\n", encoding="utf-8")
            output = root / "output"
            self.run_cli(
                cli, "render", "--input", source, "--theme", "apple-code", "--output-root", output,
                "--preserve-content", "--no-open", "--non-interactive",
            )
            manifest = json.loads((output / "article" / "manifest.json").read_text(encoding="utf-8"))
            self.assertIn("Sample body.", Path(manifest["final_article"]).read_text(encoding="utf-8"))

            config = {"wechat": {"app_id": "fixture-app", "app_secret": "fixture-secret"}}
            (target / "config.json").write_text(json.dumps(config), encoding="utf-8")
            cover = root / "cover.png"
            cover.write_bytes(b"mock cover")
            (root / "requests.py").write_text(
                """import json
from pathlib import Path
from types import SimpleNamespace

def record(event):
    with Path(__file__).with_suffix(".log").open("a", encoding="utf-8") as log:
        print(event, file=log)

def get(url, *, timeout):
    assert "/cgi-bin/token?" in url and "appid=fixture-app" in url
    record("token")
    return SimpleNamespace(json=lambda: {"access_token": "fixture-token"})

def post(url, **kwargs):
    if "/cgi-bin/media/uploadimg?" in url:
        assert kwargs["files"]["media"][1].read() == b"body image"
        record("body")
        return SimpleNamespace(json=lambda: {"url": "https://mmbiz.qpic.cn/body"})
    if "/cgi-bin/material/add_material?" in url:
        assert kwargs["files"]["media"][1].read() == b"mock cover"
        record("cover")
        return SimpleNamespace(json=lambda: {"media_id": "fixture-cover"})
    assert "/cgi-bin/draft/add?access_token=fixture-token" in url
    record("draft")
    article, = json.loads(kwargs["data"])["articles"]
    assert article["title"] == "Draft title"
    assert article["thumb_media_id"] == "fixture-cover"
    assert "Sample body." in article["content"]
    return SimpleNamespace(json=lambda: {"media_id": "fixture-draft"})
""",
                encoding="utf-8",
            )
            env = {**os.environ, "PYTHONPATH": str(root)}
            log = root / "requests.log"
            args = ("draft", "--input", source, "--output", output / "preview", "--cover", cover)
            self.run_cli(cli, *args, "--dry-run", env=env)
            self.assertFalse(log.exists(), "offline preview made an HTTP request")
            args = ("draft", "--dir", manifest["final_dir"], "--cover", cover, "--title", "Draft title")
            self.run_cli(cli, *args, "--dry-run", "--upload-only", env=env, status=2)
            self.assertFalse(log.exists())
            self.run_cli(cli, *args, "--upload-only", env=env)
            self.assertEqual(log.read_text().splitlines(), ["token", "body", "cover"])
            log.unlink()
            result = self.run_cli(cli, *args, env=env)
            self.assertEqual(log.read_text().splitlines(), ["token", "body", "cover", "draft"])
            self.assertIn("fixture-draft", result.stdout)

    def run_cli(self, cli, *args, env=None, status=0):
        result = subprocess.run(
            [sys.executable, str(cli), *map(str, args)],
            env={**(env or os.environ), "PYTHONIOENCODING": "utf-8"},
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
        self.assertEqual(result.returncode, status, result.stderr or result.stdout)
        return result
