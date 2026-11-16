import ast
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "official_format.py"


def find_officecli():
    executable = shutil.which("officecli")
    if executable:
        return executable
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidate = Path(local_app_data) / "OfficeCLI" / "officecli.exe"
        if candidate.is_file():
            return str(candidate)
    return None


def load_pure_helpers():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"), filename=str(SCRIPT))
    wanted = {"format_date", "_parse_attachment_content"}
    nodes = [node for node in tree.body if isinstance(node, ast.Import) and any(alias.name == "re" for alias in node.names)]
    nodes.extend(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted)
    namespace = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SCRIPT), "exec"), namespace)
    return namespace


class PureHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helpers = load_pure_helpers()

    def test_format_date_normalizes_supported_numeric_forms(self):
        format_date = self.helpers["format_date"]
        self.assertEqual("2026年4月16日", format_date("2026-04-16"))
        self.assertEqual("2026年4月16日", format_date("2026/04/16"))

    def test_attachment_parser_splits_numbered_items_and_strips_punctuation(self):
        parse = self.helpers["_parse_attachment_content"]
        self.assertEqual(["附件：1. 方案一", "2. 方案二"], parse("1. 方案一  2. 方案二。"))


@unittest.skipUnless(importlib.util.find_spec("docx"), "python-docx is not installed")
class DocumentGenerationTests(unittest.TestCase):
    def test_installed_convert_accepts_text_and_writes_docx(self):
        from docx import Document

        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source = folder / "source.txt"
            output = folder / "result.docx"
            source.write_text("会议安排如下。", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-c", "import official_format; raise SystemExit(official_format.cli_main())",
                 "convert", "--title", "会议通知", "--input", str(source), "--output", str(output)],
                cwd=SCRIPT.parent,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            paragraphs = [paragraph.text for paragraph in Document(output).paragraphs]
            self.assertIn("会议通知", paragraphs)
            self.assertIn("会议安排如下。", paragraphs)

    def test_docx_input_preserves_table_cells_in_document_order(self):
        from docx import Document

        spec = importlib.util.spec_from_file_location("official_format", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.docx"
            doc = Document()
            doc.add_paragraph("前置正文")
            table = doc.add_table(rows=1, cols=2)
            table.cell(0, 0).text = "姓名"
            table.cell(0, 1).text = "张三"
            doc.add_paragraph("后置正文")
            doc.save(source)
            content, is_markdown = module.read_input(source)
            self.assertFalse(is_markdown)
            self.assertLess(content.index("前置正文"), content.index("【原文表格】"))
            self.assertIn("姓名 | 张三", content)
            self.assertLess(content.index("【原文表格结束】"), content.index("后置正文"))
    def test_generates_docx_with_title_and_body(self):
        from docx import Document

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "content.txt"
            output = Path(tmp) / "output.docx"
            source.write_text("一、工作安排\n这是正文。", encoding="utf-8")
            subprocess.run(
                [sys.executable, str(SCRIPT), "--title", "测试通知", "--input", str(source), "--output", str(output)],
                check=True,
                capture_output=True,
                text=True,
            )
            text = "\n".join(paragraph.text for paragraph in Document(output).paragraphs)
            self.assertIn("测试通知", text)
            self.assertIn("这是正文。", text)
            officecli = find_officecli()
            if officecli:
                try:
                    validation = subprocess.run(
                        [officecli, "validate", str(output)],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(0, validation.returncode, validation.stdout + validation.stderr)
                    issues = subprocess.run(
                        [officecli, "view", str(output), "issues"],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(0, issues.returncode, issues.stdout + issues.stderr)
                    self.assertNotIn("Empty paragraph", issues.stdout)
                finally:
                    subprocess.run(
                        [officecli, "close", str(output)],
                        check=False,
                        capture_output=True,
                        text=True,
                    )


if __name__ == "__main__":
    unittest.main()
