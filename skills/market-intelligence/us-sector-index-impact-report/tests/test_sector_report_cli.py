import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sample-report.json"


@unittest.skipUnless(shutil.which("sector-report-render"), "Install the report renderer")
class SectorReportCommandTests(unittest.TestCase):
    def test_renders_complete_fixture_and_rejects_incomplete_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "report.html"
            subprocess.run(
                ["sector-report-render", "--input", str(FIXTURE), "--output", str(report)],
                check=True, capture_output=True, timeout=30,
            )
            payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
            html = report.read_text(encoding="utf-8")
            for expected in ("<!DOCTYPE html>", payload["session_date"], "Nasdaq Composite", "Nasdaq 100"):
                self.assertIn(expected.lower(), html.lower())

            invalid = Path(temp) / "invalid.json"
            invalid.write_text("{}", encoding="utf-8")
            report.unlink()
            result = subprocess.run(
                ["sector-report-render", "--input", str(invalid), "--output", str(report)],
                capture_output=True, timeout=30,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(report.exists())
