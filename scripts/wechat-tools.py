"""Repository CLI for WeChat article rendering and draft upload."""

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "content-operations" / "wechat-format" / "scripts"
COMMANDS = {
    "render": ("article_workflow.py", "Render a Markdown article with the WeChat workflow"),
    "draft": ("publish.py", "Check a draft offline, upload its images, or submit it to WeChat"),
}


def main():
    arguments = sys.argv[1:]
    if arguments and arguments[0] in COMMANDS:
        script, _ = COMMANDS[arguments[0]]
        return subprocess.call([sys.executable, str(SCRIPTS / script), *arguments[1:]])

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, (_, description) in COMMANDS.items():
        commands.add_parser(name, help=description)
    parser.parse_args(arguments)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
