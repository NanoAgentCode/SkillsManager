"""Check a local Dify DSL without a repository checkout or Dify credentials."""

import argparse
import json
import re
from pathlib import Path


SELECTORS = {"value_selector", "variable_selector", "query_variable_selector",
             "iterator_selector", "output_selector", "input_selector"}
TEMPLATE_REF = re.compile(r"\{\{#([^{}#\s]+)#\}\}")
NAMESPACES = {"sys", "env", "conversation"}


def references(value, location, node_type):
    """Yield (field location, selector) for variable bindings in node data."""
    if isinstance(value, dict):
        for key, item in value.items():
            field = f"{location}.{key}"
            if key in SELECTORS:
                # Dify exports empty bindings for optional context and vision inputs.
                if key == "variable_selector" and item == [] and (
                    location.endswith(".vision.configs") or value.get("enabled") is False
                ):
                    continue
                yield field, item
            elif key == "variables" and node_type == "variable-aggregator" and isinstance(item, list):
                for index, selector in enumerate(item):
                    yield f"{field}[{index}]", selector
            elif (key == "query" and node_type == "parameter-extractor" and isinstance(item, list)
                  or key == "value" and value.get("type") == "variable"):
                yield field, item
            elif key == "outputs" and node_type == "code":
                continue  # Arbitrary output names form a schema, not input bindings.
            elif key not in {"code", "desc", "title", "structured_output", "output_schema"}:
                yield from references(item, field, node_type)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from references(item, f"{location}[{index}]", node_type)
    elif isinstance(value, str):
        for match in TEMPLATE_REF.finditer(value):
            if match.group(1) != "context":  # Built-in LLM context placeholder.
                yield location, match.group(1).split(".")


def validate_reference(location, selector, nodes):
    if not isinstance(selector, list) or len(selector) < 2 or not all(
        isinstance(part, str) and part.strip() for part in selector
    ):
        return f"{location}: expected a variable selector [source, field, ...]"
    source, field, *_ = selector
    if source in NAMESPACES:
        return
    ref = ".".join(selector)
    if source not in nodes:
        return f"{location}: {ref} refers to unknown node {source}"
    data = nodes[source]
    if data.get("type") == "start":
        variables = data.get("variables", [])
        if not isinstance(variables, list) or not any(
            isinstance(var, dict) and var.get("variable") == field for var in variables
        ):
            return f"{location}: {ref} is not a declared start variable"
    if data.get("type") == "code":
        outputs = data.get("outputs", {})
        if not isinstance(outputs, dict) or (field not in outputs and field not in {"error_type", "error_message"}):
            return f"{location}: {ref} is not a declared code output"


def validate_graph(document):
    workflow = document.get("workflow") if isinstance(document, dict) else None
    graph = workflow.get("graph") if isinstance(workflow, dict) else None
    if not isinstance(graph, dict):
        return ["expected a workflow.graph mapping"]
    nodes, edges = graph.get("nodes"), graph.get("edges")
    if not isinstance(nodes, list) or not nodes:
        return ["workflow.graph.nodes must be a non-empty list"]
    if not isinstance(edges, list):
        return ["workflow.graph.edges must be a list"]

    errors = []
    node_data = {}
    for index, node in enumerate(nodes):
        node_id = node.get("id") if isinstance(node, dict) else None
        if not isinstance(node_id, str) or not node_id or node_id in node_data:
            errors.append(f"nodes[{index}]: expected a unique non-empty string id")
        elif not isinstance(node.get("data"), dict):
            errors.append(f"node {node_id}: expected a data mapping")
        else:
            node_data[node_id] = node["data"]

    edge_ids = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edges[{index}]: expected a mapping")
            continue
        edge_id = edge.get("id")
        if not isinstance(edge_id, str) or not edge_id or edge_id in edge_ids:
            errors.append(f"edges[{index}]: expected a unique non-empty string id")
        else:
            edge_ids.add(edge_id)
        if edge.get("type") != "custom" or not edge.get("sourceHandle") or not edge.get("targetHandle"):
            errors.append(f"edge {edge_id}: expected custom type and both handles")
        metadata = edge.get("data")
        for side in ("source", "target"):
            endpoint = edge.get(side)
            declared_type = metadata.get(side + "Type") if isinstance(metadata, dict) else None
            if not isinstance(endpoint, str) or endpoint not in node_data:
                errors.append(f"edge {edge_id}: {side} node {endpoint!r} does not exist")
            elif not declared_type or declared_type != node_data[endpoint].get("type"):
                errors.append(f"edge {edge_id}: {side}Type does not match node {endpoint}")

    for node_id, data in node_data.items():
        for location, selector in references(data, node_id, data.get("type")):
            error = validate_reference(location, selector, node_data)
            if error:
                errors.append(error)
    return errors


def validate_file(path):
    try:
        text = path.read_text(encoding="utf-8-sig")
        if path.suffix.lower() == ".json":
            document = json.loads(text)
        else:
            try:
                import yaml
            except ImportError:
                return ["YAML validation requires PyYAML. JSON input can be validated with Python alone."]
            try:
                document = yaml.safe_load(text)
            except yaml.YAMLError as exc:
                return [f"invalid YAML: {exc}"]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"{path}: {exc}"]
    return validate_graph(document)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Local JSON or YAML DSL file")
    args = parser.parse_args()
    errors = validate_file(args.input)
    for error in errors:
        print(f"[fail] {error}")
    if errors:
        return 1
    print(f"OK: graph and variable references checked in {args.input}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
