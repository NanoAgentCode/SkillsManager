import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


CONTENT = Path(__file__).resolve().parents[2] / "skills" / "content-operations"


class SkillOutputPathsTests(unittest.TestCase):
    def run_script(self, script, project, *args):
        return subprocess.run(
            [sys.executable, str(script), *map(str, args)],
            cwd=project,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=True,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

    def test_standalone_wechat_uses_each_project_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "installed" / "skills" / "wechat-format"
            shutil.copytree(CONTENT / "wechat-format", skill, ignore=shutil.ignore_patterns(
                "config.json", "__pycache__", "comment_state.json", "comment_reply.log",
            ))
            (skill / "config.json").write_text(json.dumps({"output_dir": str(root / "legacy-output")}), encoding="utf-8")
            for project_name in ("project-a", "project-b"):
                project = root / project_name
                project.mkdir()
                article = project / "demo.md"
                article.write_text(f"# Demo\n\nContent for {project_name}.\n", encoding="utf-8")
                scripts = skill / "scripts"
                self.run_script(scripts / "article_workflow.py", project, "--input", article,
                                "--theme", "apple-code", "--preserve-content", "--no-open", "--non-interactive")
                workflow = project / "output" / "wechat-format" / "article-workflows" / "demo"
                manifest = json.loads((workflow / "manifest.json").read_text(encoding="utf-8"))
                article_html = Path(manifest["final_article"])
                self.assertTrue(article_html.is_relative_to(workflow))
                self.assertIn(project_name, article_html.read_text(encoding="utf-8"))
                self.run_script(scripts / "format.py", project, "--input", article, "--theme", "apple-code", "--no-open")
                self.assertTrue((project / "output/wechat-format/tmp/demo/article.html").is_file())
            self.assertFalse((root / "legacy-output").exists())

    def test_subtitle_default_does_not_write_next_to_input(self):
        script = CONTENT / "video-transcriber/scripts/subtitle_to_markdown.py"
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            source = project / "inputs" / "demo.srt"
            source.parent.mkdir()
            source.write_text("1\n00:00:01,000 --> 00:00:03,000\nHello.\n", encoding="utf-8")
            self.run_script(script, project, source)
            transcript = project / "output/video-transcriber/demo/demo.md"
            self.assertIn("Hello.", transcript.read_text(encoding="utf-8"))
            self.assertFalse(source.with_suffix(".md").exists())

    def test_archive_staging_and_render_paths_use_calling_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            installed = root / "installed"
            script = installed / "wechat-history-article-archive/scripts/reformat_archived_articles.py"
            script.parent.mkdir(parents=True)
            shutil.copy2(CONTENT / "wechat-history-article-archive/scripts/reformat_archived_articles.py", script)
            formatter = installed / "wechat-format/scripts/article_workflow.py"
            formatter.parent.mkdir(parents=True)
            formatter.touch()
            project = root / "business-project"
            archive = project / "input-archive"
            article = archive / "demo" / "article.md"
            article.parent.mkdir(parents=True)
            article.write_text("# Demo\n", encoding="utf-8")
            record = {"seq": 1, "status": "ok", "markdown_path": "demo/article.md"}
            (archive / "index.json").write_text(json.dumps([record]), encoding="utf-8")
            self.run_script(script, project, "--archive-dir", archive, "--article", "1", "--dry-run")
            stage = project / "output/wechat-history-article-archive/reformat-inputs"
            self.assertTrue((stage / "demo/demo.md").is_file())
            manifest = json.loads((stage / "reformat-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(manifest["workflow_output_root"]), project / "output/wechat-format/article-workflows")
            self.assertFalse((root / "installed/output").exists())
