"""Installed entry point for WeChat article archives."""

import argparse
import sys

from archive_article_urls import main as fetch
from convert_archive_to_markdown import main as export
from extract_mp_urls import main as extract


COMMANDS = {
    "extract": (extract, "Extract and deduplicate article URLs"),
    "fetch": (fetch, "Archive authorized public articles"),
    "export": (export, "Convert archived HTML to Markdown"),
}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in COMMANDS:
        command, _ = COMMANDS[argv[0]]
        return command(argv[1:])

    parser = argparse.ArgumentParser(description="Archive authorized WeChat articles.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, (_, description) in COMMANDS.items():
        commands.add_parser(name, help=description)
    parser.parse_args(argv)
