import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


@unittest.skipUnless(shutil.which("depgraph") and shutil.which("dot"), "Install depgraph and Graphviz")
class DepgraphCommandTests(unittest.TestCase):
    def test_generates_and_validates_dependency_for_each_language(self):
        fixtures = {
            "python": {"app.py": "import helper\n", "helper.py": "VALUE = 1\n"},
            "javascript": {"app.ts": 'import "./helper";\n', "helper.ts": "export const value = 1;\n"},
            "go": {
                "go.mod": "module example.test/demo\n",
                "app.go": 'package demo\nimport _ "example.test/demo/helper"\n',
                "helper/helper.go": "package helper\n",
            },
            "rust": {"src/lib.rs": "mod helper;\nuse crate::helper::VALUE;\n", "src/helper.rs": ""},
        }
        for language, files in fixtures.items():
            with self.subTest(language=language), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                for name, content in files.items():
                    source = root / name
                    source.parent.mkdir(parents=True, exist_ok=True)
                    source.write_text(content, encoding="utf-8")
                diagram = root / "dependencies.drawio"
                subprocess.run(
                    ["depgraph", "generate", str(root), "--language", language, "--no-reduce",
                     "-o", str(diagram)], check=True, capture_output=True,
                )
                cells = ET.parse(diagram).findall(".//mxCell")
                self.assertEqual(sum(cell.get("edge") == "1" for cell in cells), 1)
                subprocess.run(["depgraph", "validate", str(diagram)], check=True, capture_output=True)

    def test_rejects_invalid_xml(self):
        with tempfile.TemporaryDirectory() as temp:
            diagram = Path(temp) / "invalid.drawio"
            diagram.write_text("<invalid", encoding="utf-8")
            result = subprocess.run(["depgraph", "validate", str(diagram)], capture_output=True)
            self.assertEqual(result.returncode, 1)
