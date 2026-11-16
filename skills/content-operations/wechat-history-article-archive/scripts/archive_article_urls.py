#!/usr/bin/env python3
"""Archive self-owned WeChat article URLs into local HTML and metadata files."""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path

from markdown_export import export_article_markdown

TITLE_RE = re.compile(r'<meta\s+property="og:title"\s+content="([^"]+)"', re.IGNORECASE)
DESC_RE = re.compile(r'<meta\s+property="og:description"\s+content="([^"]*)"', re.IGNORECASE)
URL_RE = re.compile(r'<meta\s+property="og:url"\s+content="([^"]+)"', re.IGNORECASE)
NICK_RE = re.compile(r'var\s+nickname\s*=\s*htmlDecode\("([^"]*)"\)', re.IGNORECASE)
USER_RE = re.compile(r'var\s+user_name\s*=\s*"([^"]*)"', re.IGNORECASE)
CT_RE = re.compile(r'\bvar\s+ct\s*=\s*"?(?P<value>\d{8,12})"?', re.IGNORECASE)
INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def load_urls(path: Path) -> list[str]:
    if path.suffix.lower() == ".json":
        return [item.strip() for item in json.loads(path.read_text(encoding="utf-8")) if str(item).strip()]
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def extract(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    value = match.groupdict().get("value") or match.group(1)
    return unescape(value).strip()


def slugify(index: int, title: str) -> str:
    base = INVALID_CHARS_RE.sub("-", title).strip().strip(".")
    base = re.sub(r"\s+", "-", base)
    base = re.sub(r"-{2,}", "-", base)
    if not base:
        base = f"article-{index:04d}"
    return f"{index:04d}-{base[:80]}"


def fetch(url: str, timeout: int, user_agent: str) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset, errors="replace")
        return response.status, body


def write_index_json(records: list[dict], output_dir: Path) -> None:
    (output_dir / "index.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def write_index_csv(records: list[dict], output_dir: Path) -> None:
    fieldnames = [
        "seq",
        "title",
        "nickname",
        "user_name",
        "publish_ct",
        "source_url",
        "status",
        "error",
        "article_dir",
        "markdown_path",
        "images_dir",
        "image_count",
    ]
    with (output_dir / "index.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({key: record.get(key, "") for key in fieldnames})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Archive WeChat article URLs into local HTML and metadata files.")
    parser.add_argument("--input", "-i", required=True, help="Input URL list (.txt or .json)")
    parser.add_argument("--output-dir", "-o", required=True, help="Archive output directory")
    parser.add_argument("--pause-ms", type=int, default=800, help="Pause between requests in milliseconds")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    parser.add_argument("--keep-html", action="store_true", help="Keep intermediate article.html files")
    parser.add_argument(
        "--user-agent",
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        help="User-Agent header",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    articles_dir = output_dir / "articles"
    output_dir.mkdir(parents=True, exist_ok=True)
    articles_dir.mkdir(parents=True, exist_ok=True)

    urls = load_urls(input_path)
    records: list[dict] = []

    for index, url in enumerate(urls, start=1):
        record = {
            "seq": index,
            "source_url": url,
            "status": "pending",
            "error": "",
            "title": "",
            "nickname": "",
            "user_name": "",
            "publish_ct": "",
            "article_dir": "",
        }
        try:
            status_code, html_text = fetch(url, timeout=args.timeout, user_agent=args.user_agent)
            title = extract(TITLE_RE, html_text) or f"article-{index:04d}"
            article_slug = slugify(index, title)
            article_dir = articles_dir / article_slug
            article_dir.mkdir(parents=True, exist_ok=True)

            metadata = {
                "seq": index,
                "title": title,
                "description": extract(DESC_RE, html_text),
                "canonical_url": extract(URL_RE, html_text) or url,
                "source_url": url,
                "nickname": extract(NICK_RE, html_text),
                "user_name": extract(USER_RE, html_text),
                "publish_ct": extract(CT_RE, html_text),
                "status_code": status_code,
            }
            metadata = export_article_markdown(
                article_dir=article_dir,
                html_text=html_text,
                metadata=metadata,
                user_agent=args.user_agent,
                timeout=args.timeout,
            )
            (article_dir / "meta.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            if args.keep_html:
                (article_dir / "article.html").write_text(html_text, encoding="utf-8")

            record.update(
                {
                    "status": "ok",
                    "title": metadata["title"],
                    "nickname": metadata["nickname"],
                    "user_name": metadata["user_name"],
                    "publish_ct": metadata["publish_ct"],
                    "article_dir": str(article_dir),
                    "markdown_path": metadata.get("markdown_path", ""),
                    "images_dir": metadata.get("images_dir", ""),
                    "image_count": metadata.get("image_count", 0),
                }
            )
        except urllib.error.HTTPError as exc:
            record.update({"status": "http_error", "error": f"{exc.code} {exc.reason}"})
        except urllib.error.URLError as exc:
            record.update({"status": "url_error", "error": str(exc.reason)})
        except Exception as exc:  # noqa: BLE001
            record.update({"status": "error", "error": str(exc)})

        records.append(record)
        time.sleep(max(args.pause_ms, 0) / 1000)

    write_index_json(records, output_dir)
    write_index_csv(records, output_dir)

    ok_count = sum(1 for item in records if item["status"] == "ok")
    print(f"Archived {ok_count}/{len(records)} article(s) into {output_dir}")
    return 0 if ok_count == len(records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
