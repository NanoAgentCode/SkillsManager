#!/usr/bin/env python3
"""Convert archived WeChat article HTML files into Markdown and local images."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from markdown_export import export_article_markdown


def update_index_csv(archive_dir: Path, records: list[dict]) -> None:
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
    with (archive_dir / "index.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({key: record.get(key, "") for key in fieldnames})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Convert archived WeChat article HTML files into Markdown and local images.")
    parser.add_argument("--archive-dir", required=True, help="Archive directory containing index.json and articles/")
    parser.add_argument("--timeout", type=int, default=20, help="Image download timeout in seconds")
    parser.add_argument("--delete-html", action="store_true", help="Delete article.html after successful conversion")
    parser.add_argument(
        "--user-agent",
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        help="User-Agent header",
    )
    args = parser.parse_args(argv)

    archive_dir = Path(args.archive_dir)
    records = json.loads((archive_dir / "index.json").read_text(encoding="utf-8"))
    converted = 0
    invalid = 0

    for record in records:
        if record.get("status") != "ok":
            continue
        article_dir = Path(record["article_dir"])
        html_path = article_dir / "article.html"
        meta_path = article_dir / "meta.json"
        if not html_path.exists() or not meta_path.exists():
            continue

        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        try:
            metadata = export_article_markdown(
                article_dir=article_dir,
                html_text=html_path.read_text(encoding="utf-8"),
                metadata=metadata,
                user_agent=args.user_agent,
                timeout=args.timeout,
            )
        except ValueError as exc:
            record.update({"status": "invalid_article", "error": str(exc)})
            invalid += 1
            continue
        meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.delete_html and html_path.exists():
            html_path.unlink()
        record.update(
            {
                "title": metadata.get("title", record.get("title", "")),
                "nickname": metadata.get("nickname", record.get("nickname", "")),
                "markdown_path": metadata.get("markdown_path", ""),
                "images_dir": metadata.get("images_dir", ""),
                "image_count": metadata.get("image_count", 0),
            }
        )
        converted += 1

    (archive_dir / "index.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    update_index_csv(archive_dir, records)
    print(f"Converted {converted} article(s) into Markdown under {archive_dir}; {invalid} invalid article(s)")
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
