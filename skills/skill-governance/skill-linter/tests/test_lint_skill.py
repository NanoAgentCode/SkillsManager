import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[4]
LINTER_PATH = (
    REPO_ROOT
    / "skills"
    / "skill-governance"
    / "skill-linter"
    / "scripts"
    / "lint_skill.py"
)

spec = importlib.util.spec_from_file_location("lint_skill", LINTER_PATH)
lint_skill = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = lint_skill
spec.loader.exec_module(lint_skill)


def write_skill(root: Path) -> None:
    skill_dir = root / "demo-skill"
    (skill_dir / "agents").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: demo-skill
description: Use when validating that repository compatibility entrypoints are checked by the linter.
---

# Demo Skill

Follow this demo workflow when testing repository-level linter behavior. The body is intentionally long enough
to avoid thin-body warnings while keeping the fixture easy to understand and maintain during future changes.
""",
        encoding="utf-8",
    )
    (skill_dir / "agents" / "openai.yaml").write_text(
        """interface:
  display_name: "Demo Skill"
  short_description: "Demo metadata"
  default_prompt: "Use $demo-skill for this demo."
""",
        encoding="utf-8",
    )


class SecretHygieneTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("git"), "requires Git ignore and index checks")
    def test_local_config_is_skipped_only_when_git_ignores_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            skill_dir = root / "demo-skill"
            skill_dir.mkdir()
            value = "fixture-" + "secret-123456789"
            config = skill_dir / "config.json"
            config.write_text(json.dumps({"example": f"api_key = {value}"}), encoding="utf-8")
            ignore_file = skill_dir / ".gitignore"
            ignore_file.write_text("!config.json\n", encoding="utf-8")
            expected_codes = {"local-config-file", "possible-secret"}
            self.assertEqual(
                {item.code for item in lint_skill.check_secret_hygiene(skill_dir, root)},
                expected_codes,
            )

            ignore_file.write_text("config.json\n", encoding="utf-8")
            self.assertEqual(lint_skill.check_secret_hygiene(skill_dir, root), [])

            subprocess.run(["git", "add", "-f", "--", str(config)], cwd=root, check=True)
            self.assertEqual(
                {item.code for item in lint_skill.check_secret_hygiene(skill_dir, root)},
                expected_codes,
            )


class RepositoryEntrypointTests(unittest.TestCase):
    def test_docs_skill_index_satisfies_catalog_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_skill(root)
            (root / "docs").mkdir()
            (root / "docs" / "skill-index.md").write_text(
                "- `demo-skill/SKILL.md`: repository compatibility validation.\n",
                encoding="utf-8",
            )
            skill_dir = root / "demo-skill"
            frontmatter = {"name": "demo-skill"}
            findings = lint_skill.check_repo_catalog(skill_dir, root, frontmatter, root)

        self.assertEqual(findings, [])

    def test_primary_catalog_requires_the_exact_path_even_when_readme_names_the_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills" / "tools" / "demo-skill"
            skill.mkdir(parents=True)
            index = root / "docs" / "skill-index.md"
            index.parent.mkdir()
            (root / "README.md").write_text("demo-skill", encoding="utf-8")
            meta = {"name": "demo-skill"}
            for entry in ("demo-skill", "skills/old/demo-skill/SKILL.md",
                          "skills/tools/demo-skill/SKILL.md.bak", "other/skills/tools/demo-skill/SKILL.md"):
                with self.subTest(entry=entry):
                    index.write_text(f"- `{entry}`\n", encoding="utf-8")
                    findings = lint_skill.check_repo_catalog(skill, root, meta, root)
                    self.assertEqual([item.code for item in findings], ["catalog-not-synced"])
            index.write_text("- [Demo](../skills/tools/demo-skill/SKILL.md)\n", encoding="utf-8")
            self.assertEqual(lint_skill.check_repo_catalog(skill, root, meta, root), [])
            index.unlink()
            self.assertEqual(lint_skill.check_repo_catalog(skill, root, meta, root), [])

    def test_missing_platform_entrypoint_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            findings = lint_skill.check_repository_entrypoints(root, root)

        self.assertEqual(len(findings), 4)
        self.assertIn("missing-agents-guide", {item.code for item in findings})
        platform_findings = [item for item in findings if item.code == "missing-platform-entrypoint"]
        self.assertEqual(len(platform_findings), 3)
        self.assertIn("CLAUDE.md", {item.path for item in findings})

    def test_stale_platform_entrypoint_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "AGENTS.md").write_text(
                "Use SKILL.md with CLAUDE.md, GEMINI.md, and GLM.md.\n",
                encoding="utf-8",
            )
            for filename in lint_skill.REPOSITORY_ENTRYPOINTS:
                (root / filename).write_text("Read this repository README only.\n", encoding="utf-8")

            findings = lint_skill.check_repository_entrypoints(root, root)

        self.assertEqual(len(findings), 3)
        self.assertTrue(all(item.code == "stale-platform-entrypoint" for item in findings))
        self.assertIn("AGENTS.md", findings[0].message)
        self.assertIn("SKILL.md", findings[0].message)

    def test_cli_reports_repository_entrypoints_with_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_skill(root)
            (root / "README.md").write_text("demo-skill\n", encoding="utf-8")
            (root / "AGENTS.md").write_text(
                "Use SKILL.md with CLAUDE.md, GEMINI.md, and GLM.md.\n",
                encoding="utf-8",
            )
            for filename in lint_skill.REPOSITORY_ENTRYPOINTS:
                (root / filename).write_text(
                    "Read AGENTS.md, then read the selected SKILL.md.\n",
                    encoding="utf-8",
                )
            (root / "GLM.md").write_text("Read AGENTS.md only.\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(LINTER_PATH),
                    str(root),
                    "--repo-root",
                    str(root),
                    "--json",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn(".", payload)
        repo_codes = {item["code"] for item in payload["."]}
        self.assertEqual(repo_codes, {"stale-platform-entrypoint"})

    def test_current_repository_entrypoints_are_fresh(self) -> None:
        findings = lint_skill.check_repository_entrypoints(REPO_ROOT, REPO_ROOT)
        self.assertEqual(findings, [])


class InstalledCommandTests(unittest.TestCase):
    def test_check_returns_json_and_strict_exit_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_skill(root)
            (root / "demo-skill" / "agents" / "openai.yaml").unlink()
            args = ["skill-lint", "check", temp, "--json"]
            for options, expected in (([], 0), (["--strict"], 1)):
                with self.subTest(options=options):
                    with patch.object(sys, "argv", args + options), patch("builtins.print") as output:
                        self.assertEqual(lint_skill.cli_main(), expected)
                    findings = json.loads(output.call_args.args[0])["demo-skill"]
                    self.assertTrue(any(item["severity"] == "warning" for item in findings))

    def test_missing_target_returns_usage_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(sys, "argv", ["skill-lint", "check", temp]), patch("builtins.print"):
                self.assertEqual(lint_skill.cli_main(), 2)


if __name__ == "__main__":
    unittest.main()
