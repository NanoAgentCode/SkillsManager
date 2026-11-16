import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


CLI = Path(__file__).resolve().parents[1] / "knowledge-tools.ps1"


@unittest.skipUnless(shutil.which("pwsh"), "PowerShell 7 is required")
class KnowledgeToolsTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            ["pwsh", "-NoProfile", "-File", str(CLI), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )

    @unittest.skipUnless(shutil.which("markmap") or shutil.which("markmap.cmd"), "markmap CLI is required")
    def test_render_and_publish_to_temporary_static_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            markdown = root / "sample outline.md"
            html = root / "sample mindmap.html"
            markdown.write_text("# Parent\n\n- Child\n", encoding="utf-8")
            render = self.run_cli("mindmap-render", "-InputMarkdown", markdown, "-OutputHtml", html)
            self.assertEqual(render.returncode, 0, render.stderr)
            content = html.read_text(encoding="utf-8-sig")
            self.assertIn("Child", content)
            self.assertNotRegex(content, r'<script[^>]+src="https?://')

            static = root / "static"
            publish = self.run_cli(
                "mindmap-publish", "-SourceHtml", html, "-StaticRoot", static,
                "-PublicBaseUrl", "https://example.test", "-PathPrefix", "/maps", "-Slug", "demo",
            )
            self.assertEqual(publish.returncode, 0, publish.stderr)
            self.assertEqual(json.loads(publish.stdout)["url"], "https://example.test/maps/demo/index.html")
            self.assertEqual((static / "demo" / "index.html").read_bytes(), html.read_bytes())

    def test_search_reindex_and_report_audit_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "demo vault"
            note = vault / "20-Knowledge" / "demo-note.md"
            note.parent.mkdir(parents=True)
            note.write_text("# Demo note\n\nUnique query phrase\n", encoding="utf-8")
            search = self.run_cli("vault-search", "-VaultPath", vault, "-Query", "Unique,phrase")
            self.assertEqual(search.returncode, 0, search.stderr)
            self.assertIn("demo-note.md", search.stdout)

            reindex = self.run_cli("vault-reindex", "-VaultPath", vault)
            self.assertEqual(reindex.returncode, 0, reindex.stderr)
            index = vault / "90-System" / "Codex-Memory-Index.md"
            self.assertIn("20-Knowledge/demo-note", index.read_text(encoding="utf-8"))

            audit = self.run_cli("vault-audit", "-VaultPath", vault, "-Json")
            self.assertEqual(audit.returncode, 1, audit.stderr)
            self.assertIn("demo-note.md", audit.stdout)
            self.assertIsInstance(json.loads(audit.stdout), dict)
