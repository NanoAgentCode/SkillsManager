from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "quick_validate.py"
SPEC = importlib.util.spec_from_file_location("quick_validate", SCRIPT)
assert SPEC and SPEC.loader
quick_validate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(quick_validate)


def workflow() -> dict:
    return {
        "workflow": {
            "graph": {
                "nodes": [
                    {"id": "start", "data": {"type": "start"}},
                    {"id": "end", "data": {"type": "end"}},
                ],
                "edges": [
                    {
                        "id": "start-source-end-target",
                        "source": "start",
                        "sourceHandle": "source",
                        "target": "end",
                        "targetHandle": "target",
                        "type": "custom",
                        "data": {"sourceType": "start", "targetType": "end"},
                    }
                ],
            }
        }
    }


class ConsoleAdminValidationTests(unittest.TestCase):
    def test_linked_operation_reference_satisfies_console_contract(self) -> None:
        validator = quick_validate.Validator()
        quick_validate.validate_console_admin_skill(validator)
        self.assertEqual(validator.errors, [])

    def test_import_route_does_not_satisfy_create_route(self) -> None:
        skill_path = Path("skills/ai-application-delivery/dify-console-admin-api")
        source = quick_validate.ROOT / skill_path
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / skill_path
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text((source / "SKILL.md").read_text(encoding="utf-8"), encoding="utf-8")
            reference = Path("references/api-operations.md")
            operations = (source / reference).read_text(encoding="utf-8")
            (skill / reference).write_text(operations.replace('/console/api/apps"', '/other"'), encoding="utf-8")

            validator = quick_validate.Validator()
            with patch.object(quick_validate, "ROOT", root):
                quick_validate.validate_console_admin_skill(validator)

        self.assertEqual(validator.errors, ["dify-console-admin-api documents /console/api/apps"])


class GeneratedDslValidationTests(unittest.TestCase):
    def test_missing_selector_source_fails_the_repository_cli(self) -> None:
        payload = workflow()
        payload["workflow"]["graph"]["nodes"][1]["data"]["outputs"] = [
            {"variable": "answer", "value_selector": ["missing-node", "result"]}
        ]
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "app.json"
            source.write_text(json.dumps(payload), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "--input", str(source)],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("missing-node.result", result.stdout)

    def test_validator_runs_from_an_independently_installed_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "installed" / "dify-dsl-app-builder"
            shutil.copytree(SCRIPT.parent / skill.name, skill)
            project = root / "project"
            project.mkdir()
            source = project / "app.json"
            validator = skill / "scripts" / "validate_dsl.py"
            payload = workflow()
            start, end = payload["workflow"]["graph"]["nodes"]
            start["data"]["variables"] = [{"variable": "query"}]
            end["data"]["outputs"] = [{"value_selector": ["start", "query"], "variable": "answer"}]
            for field, status in (("query", 0), ("typo", 1)):
                end["data"]["outputs"][0]["value_selector"][1] = field
                source.write_text(json.dumps(payload), encoding="utf-8")
                result = subprocess.run([sys.executable, str(validator), "--input", source.name],
                                        cwd=project, capture_output=True, text=True)
                self.assertEqual(result.returncode, status, result.stderr or result.stdout)
                if status:
                    self.assertIn("start.typo", result.stdout)

    def test_json_input_checks_edges_against_node_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.json"
            path.write_text(json.dumps(workflow()), encoding="utf-8")
            validator = quick_validate.Validator()
            quick_validate.validate_workflow_input(validator, path)
            self.assertEqual([], validator.errors)

    def test_mismatched_edge_type_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.json"
            payload = workflow()
            payload["workflow"]["graph"]["edges"][0]["data"]["targetType"] = "code"
            path.write_text(json.dumps(payload), encoding="utf-8")
            validator = quick_validate.Validator()
            quick_validate.validate_workflow_input(validator, path)
            self.assertTrue(any("targetType does not match node end" in error for error in validator.errors))

    def test_templates_scopes_and_inactive_vision_binding(self) -> None:
        payload = workflow()
        start, end = payload["workflow"]["graph"]["nodes"]
        start["data"]["variables"] = [{"variable": "query"}]
        end["data"].update(answer="{{#start.query#}} {{#sys.query#}} {{#env.TOKEN#}} "
                                  "{{#conversation.state#}} {{#context#}}",
                           vision={"enabled": False, "configs": {"variable_selector": []}})
        self.assertEqual(quick_validate.validate_graph(payload), [])
        end["data"]["answer"] = "{{#unknown.text#}}"
        self.assertIn("unknown.text", quick_validate.validate_graph(payload)[0])

    def test_yaml_requires_a_parser_and_invalid_input_has_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "app.yml"
            source.write_text("workflow: {}", encoding="utf-8")
            with patch.dict(sys.modules, {"yaml": None}):
                self.assertIn("requires PyYAML", quick_validate.validate_file(source)[0])
            source = source.with_suffix(".json")
            for invalid in ("{", '{"workflow": null}', '{"workflow": {"graph": {"nodes": 1}}}'):
                source.write_text(invalid, encoding="utf-8")
                self.assertTrue(quick_validate.validate_file(source))

    def test_declared_code_output_names_are_not_input_selectors(self) -> None:
        payload = workflow()
        nodes = payload["workflow"]["graph"]["nodes"]
        nodes.append({"id": "code", "data": {"type": "code", "outputs": {"value_selector": {"type": "string"}}}})
        nodes[1]["data"]["outputs"] = [{"value_selector": ["code", "value_selector"]}]
        self.assertEqual(quick_validate.validate_graph(payload), [])
        nodes[1]["data"]["outputs"][0]["value_selector"][1] = "missing"
        self.assertIn("code.missing", quick_validate.validate_graph(payload)[0])


if __name__ == "__main__":
    unittest.main()
