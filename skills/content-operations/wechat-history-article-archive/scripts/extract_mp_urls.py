#!/usr/bin/env python3
"""Extract and normalize WeChat article URLs from mixed text input."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

URL_RE = re.compile(r"https?://mp\.weixin\.qq\.com/s\?[^\s\"'<>]+", re.IGNORECASE)


def normalize_url(raw: str) -> str:
    value = html.unescape(raw.strip())
    value = value.replace("\\/", "/")
    value = value.replace("&amp;", "&")
    value = value.rstrip("),.;]")
    return value


def extract_urls(text: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for match in URL_RE.findall(text):
        url = normalize_url(match)
        if url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Extract WeChat mp.weixin article URLs from text.")
    parser.add_argument("--input", "-i", required=True, help="Input text/HTML/source file path")
    parser.add_argument("--output", "-o", required=True, help="Output .txt or .json path")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    text = input_path.read_text(encoding="utf-8")
    urls = extract_urls(text)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".json":
        output_path.write_text(json.dumps(urls, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        output_path.write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")

    print(f"Extracted {len(urls)} URL(s) to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
