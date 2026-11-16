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


@unittest.skipUnless(importlib.util.find_spec("markdown"), "Install markdown to test the renderer")
class WechatToolsTests(unittest.TestCase):
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
            source.write_text("# Sample article\n\nSample body.\n", encoding="utf-8")
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
from types import SimpleNamespace

def get(url, *, timeout):
    assert "/cgi-bin/token?" in url and "appid=fixture-app" in url
    return SimpleNamespace(json=lambda: {"access_token": "fixture-token"})

def post(url, **kwargs):
    if "/cgi-bin/material/add_material?" in url:
        assert kwargs["files"]["media"][1].read() == b"mock cover"
        return SimpleNamespace(json=lambda: {"media_id": "fixture-cover"})
    assert "/cgi-bin/draft/add?access_token=fixture-token" in url
    article, = json.loads(kwargs["data"])["articles"]
    assert article["title"] == "Draft title"
    assert article["thumb_media_id"] == "fixture-cover"
    assert "Sample body." in article["content"]
    return SimpleNamespace(json=lambda: {"media_id": "fixture-draft"})
""",
                encoding="utf-8",
            )
            result = self.run_cli(
                cli, "draft", "--dir", manifest["final_dir"], "--cover", cover, "--title", "Draft title",
                env={**os.environ, "PYTHONPATH": str(root)},
            )
            self.assertIn("fixture-draft", result.stdout)

    def run_cli(self, cli, *args, env=None):
        result = subprocess.run(
            [sys.executable, str(cli), *map(str, args)],
            env={**(env or os.environ), "PYTHONIOENCODING": "utf-8"},
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return result
