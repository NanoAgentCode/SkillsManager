from __future__ import annotations

import importlib.util
import json
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
            self.assertTrue(any("type metadata matches nodes" in error for error in validator.errors))


if __name__ == "__main__":
    unittest.main()
