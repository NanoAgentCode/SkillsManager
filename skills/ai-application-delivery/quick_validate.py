#!/usr/bin/env python3
"""Quick repository checks for the Dify skills.

This intentionally stays small and dependency-light. If PyYAML is installed it
also validates the sample workflow structure; otherwise it falls back to text
checks so the script remains usable on a fresh Python install.
"""

from __future__ import annotations

import re
import sys
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class Validator:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.checked = 0

    def check(self, condition: bool, message: str) -> None:
        self.checked += 1
        if condition:
            print(f"[ok] {message}")
        else:
            self.errors.append(message)
            print(f"[fail] {message}")

    def require_file(self, relative_path: str) -> Path:
        path = ROOT / relative_path
        self.check(path.is_file(), f"{relative_path} exists")
        return path

    def require_dir(self, relative_path: str) -> Path:
        path = ROOT / relative_path
        self.check(path.is_dir(), f"{relative_path} exists")
        return path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, flags=re.S)
    if not match:
        return {}

    data: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def validate_skill_frontmatter(v: Validator, relative_path: str, expected_name: str) -> str:
    skill = v.require_file(relative_path)
    text = read_text(skill) if skill.is_file() else ""
    meta = frontmatter(text)
    v.check(meta.get("name") == expected_name, f"{relative_path} frontmatter name is {expected_name}")
    v.check(bool(meta.get("description")), f"{relative_path} frontmatter has description")
    return text


def validate_console_admin_skill(v: Validator) -> None:
    skill_path = "skills/ai-application-delivery/dify-console-admin-api"
    text = validate_skill_frontmatter(
        v,
        f"{skill_path}/SKILL.md",
        "dify-console-admin-api",
    )

    for term in ("ADMIN_API_KEY", "DIFY_BASE_URL", "WORKSPACE_ID", "include_secret"):
        v.check(term in text, f"dify-console-admin-api documents {term}")

    operations_ref = "references/api-operations.md"
    v.check(f"]({operations_ref})" in text, "dify-console-admin-api links api-operations.md")
    operations_path = v.require_file(f"{skill_path}/{operations_ref}")
    if not operations_path.is_file():
        return

    operations = read_text(operations_path)
    for header in ("Authorization: Bearer", "X-WORKSPACE-ID"):
        v.check(header in operations, f"dify-console-admin-api documents {header}")
    for endpoint in ("/console/api/apps", "/console/api/apps/imports"):
        pattern = rf"{re.escape(endpoint)}(?![\w/.-])"
        v.check(bool(re.search(pattern, operations)), f"dify-console-admin-api documents {endpoint}")


def validate_dsl_app_builder_skill(v: Validator) -> None:
    skill_dir = v.require_dir("skills/ai-application-delivery/dify-dsl-app-builder")
    text = validate_skill_frontmatter(
        v,
        "skills/ai-application-delivery/dify-dsl-app-builder/SKILL.md",
        "dify-dsl-app-builder",
    )

    required_refs = [
        "nodes-basic.md",
        "nodes-logic.md",
        "nodes-processing.md",
        "nodes-ai.md",
        "nodes-external.md",
        "dsl-import-rules.md",
    ]
    for ref in required_refs:
        v.check((skill_dir / ref).is_file(), f"dify-dsl-app-builder reference {ref} exists")
        v.check(ref in text, f"dify-dsl-app-builder links {ref}")

    admin_ref = "skills/ai-application-delivery/dify-console-admin-api/SKILL.md"
    v.check(admin_ref in text, "dify-dsl-app-builder references console admin skill")
    v.check((ROOT / admin_ref).is_file(), "console admin skill reference resolves")

    expected_terms = [
        "workflow",
        "advanced-chat",
        "include_secret=false",
        "覆盖导入",
        "重新导出",
    ]
    for term in expected_terms:
        v.check(term in text, f"dify-dsl-app-builder documents {term}")


def validate_readme_dify_paths(v: Validator) -> None:
    readme = v.require_file("README.md")
    text = read_text(readme) if readme.is_file() else ""
    for relative_path in [
        "skills/ai-application-delivery/dify-console-admin-api",
        "skills/ai-application-delivery/dify-dsl-app-builder",
        "skills/ai-application-delivery/dify-dsl-app-builder/dsl-import-rules.md",
    ]:
        v.check(relative_path in text, f"README references {relative_path}")
        v.check((ROOT / relative_path).exists(), f"README path {relative_path} resolves")


def validate_workflow_with_pyyaml(v: Validator, workflow_path: Path) -> bool:
    try:
        import yaml  # type: ignore
    except Exception:
        return False

    with workflow_path.open("r", encoding="utf-8") as handle:
        workflow = yaml.safe_load(handle)

    v.check(isinstance(workflow, dict), "sample workflow parses as YAML mapping")
    if not isinstance(workflow, dict):
        return True

    graph = workflow.get("workflow", {}).get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_ids = {node.get("id") for node in nodes if isinstance(node, dict)}
    node_types = {node.get("data", {}).get("type") for node in nodes if isinstance(node, dict)}

    v.check(workflow.get("kind") == "app", "sample workflow kind is app")
    v.check(isinstance(nodes, list) and len(nodes) >= 2, "sample workflow has nodes")
    v.check(isinstance(edges, list) and len(edges) >= 1, "sample workflow has edges")
    v.check({"start", "end"}.issubset(node_types), "sample workflow has start and end nodes")
    v.check(len(node_ids) == len(nodes), "sample workflow node ids are unique")

    for edge in edges:
        if not isinstance(edge, dict):
            v.check(False, "sample workflow edge is a mapping")
            continue
        edge_id = edge.get("id", "<missing id>")
        v.check(edge.get("source") in node_ids, f"edge {edge_id} source resolves")
        v.check(edge.get("target") in node_ids, f"edge {edge_id} target resolves")
        v.check(edge.get("type") == "custom", f"edge {edge_id} type is custom")
    return True


def validate_workflow_text_fallback(v: Validator, text: str) -> None:
    required_terms = [
        "kind: app",
        "version:",
        "workflow:",
        "graph:",
        "edges:",
        "nodes:",
        "type: start",
        "type: end",
        "source:",
        "target:",
    ]
    for term in required_terms:
        v.check(term in text, f"sample workflow contains {term}")


def validate_sample_workflow(v: Validator) -> None:
    workflow_path = v.require_file("skills/ai-application-delivery/context-json-validator-workflow.yml")
    if not workflow_path.is_file():
        return

    if not validate_workflow_with_pyyaml(v, workflow_path):
        print("[info] PyYAML is not installed; using text-only workflow checks")
        validate_workflow_text_fallback(v, read_text(workflow_path))


def validate_workflow_input(v: Validator, workflow_path: Path) -> None:
    """Validate a user-generated DSL when a parser is available."""
    v.check(workflow_path.is_file(), f"input DSL {workflow_path} exists")
    if not workflow_path.is_file():
        return
    if workflow_path.suffix.lower() == ".json":
        workflow = json.loads(read_text(workflow_path))
    else:
        try:
            import yaml  # type: ignore
        except Exception:
            print("[info] PyYAML is not installed; using text-only checks for YAML --input DSL")
            validate_workflow_text_fallback(v, read_text(workflow_path))
            return
        workflow = yaml.safe_load(read_text(workflow_path))
    if not isinstance(workflow, dict):
        v.check(False, "input DSL parses as a mapping")
        return
    graph = workflow.get("workflow", {}).get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    v.check(isinstance(nodes, list) and bool(nodes), "input DSL has nodes")
    v.check(isinstance(edges, list), "input DSL has edges")
    node_map = {node.get("id"): node for node in nodes if isinstance(node, dict) and node.get("id")}
    v.check(len(node_map) == len(nodes), "input DSL node ids are unique and present")
    edge_ids = [edge.get("id") for edge in edges if isinstance(edge, dict)]
    v.check(len(edge_ids) == len(set(edge_ids)) and all(edge_ids), "input DSL edge ids are unique and present")
    for edge in edges:
        if not isinstance(edge, dict):
            v.check(False, "input DSL edge is a mapping")
            continue
        source, target = edge.get("source"), edge.get("target")
        data = edge.get("data") if isinstance(edge.get("data"), dict) else {}
        v.check(source in node_map and target in node_map, f"edge {edge.get('id', '<missing>')} endpoints resolve")
        v.check(edge.get("type") == "custom" and edge.get("sourceHandle") and edge.get("targetHandle"), f"edge {edge.get('id', '<missing>')} has type and handles")
        if source in node_map and target in node_map:
            source_type = node_map[source].get("data", {}).get("type")
            target_type = node_map[target].get("data", {}).get("type")
            v.check(data.get("sourceType") == source_type and data.get("targetType") == target_type, f"edge {edge.get('id', '<missing>')} type metadata matches nodes")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Dify skill resources or one generated DSL.")
    parser.add_argument("--input", help="Generated Dify DSL in JSON, or YAML when PyYAML is installed")
    args = parser.parse_args()
    print(f"[info] Python executable: {sys.executable}")
    v = Validator()
    validate_console_admin_skill(v)
    validate_dsl_app_builder_skill(v)
    validate_readme_dify_paths(v)
    if args.input:
        validate_workflow_input(v, Path(args.input))
    else:
        validate_sample_workflow(v)

    print()
    if v.errors:
        print(f"FAILED: {len(v.errors)} of {v.checked} checks failed")
        for error in v.errors:
            print(f"- {error}")
        return 1

    print(f"OK: {v.checked} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
