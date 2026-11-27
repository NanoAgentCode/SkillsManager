"""Installed entry point for code dependency diagrams."""

import argparse
from pathlib import Path
import sys
import tempfile

from . import autolayout, goimports, jsimports, pyimports, rustimports, validate


IMPORTERS = {
    "python": pyimports.main,
    "javascript": jsimports.main,
    "go": goimports.main,
    "rust": rustimports.main,
}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["validate"]:
        return validate.main(argv[1:])

    parser = argparse.ArgumentParser(description="Generate or validate editable dependency diagrams.")
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="Extract dependencies and lay out a .drawio diagram")
    generate.add_argument("source", help="Project, source, module, or crate directory")
    generate.add_argument("--language", required=True, choices=IMPORTERS)
    generate.add_argument("-o", "--output", type=Path, required=True)
    generate.add_argument("--direction", choices=["TB", "LR"], default="TB")
    generate.add_argument("--group", action="store_true")
    generate.add_argument("--no-reduce", action="store_true")
    commands.add_parser("validate", help="Validate an existing .drawio file")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as temp:
        graph = str(Path(temp) / "graph.json")
        options = [args.source, "--output", graph, "--direction", args.direction]
        if args.group:
            options.append("--group")
        if args.no_reduce:
            options.append("--no-reduce")
        IMPORTERS[args.language](options)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        autolayout.main([graph, "--output", str(args.output)])
    return 0
