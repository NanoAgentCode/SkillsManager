#!/usr/bin/env python3
"""Stage archived WeChat articles and run the repo-local formatter workflow."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ARCHIVE_SKILL_DIR = SCRIPT_DIR.parent
FORMAT_WORKFLOW = ARCHIVE_SKILL_DIR.with_name("wechat-format") / "scripts" / "article_workflow.py"
DEFAULT_STAGE_ROOT = "output/wechat-history-article-archive/reformat-inputs"
DEFAULT_WORKFLOW_ROOT = "output/wechat-format/article-workflows"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reformat archived WeChat article Markdown through wechat-format/scripts/article_workflow.py."
    )
    parser.add_argument("--archive-dir", required=True, help="Archive directory containing index.json and articles/")
    parser.add_argument(
        "--article",
        action="append",
        default=[],
        help="Article selector. Repeatable. Matches seq, title, article directory name, or markdown filename stem.",
    )
    parser.add_argument(
        "--stage-root",
        default=str(DEFAULT_STAGE_ROOT),
        help="Directory for formatter-ready staged Markdown/images",
    )
    parser.add_argument(
        "--workflow-output-root",
        default=str(DEFAULT_WORKFLOW_ROOT),
        help="Output root passed to article_workflow.py",
    )
    parser.add_argument("--theme", help="Final theme ID passed to article_workflow.py")
    parser.add_argument("--recommend", nargs="*", help="Theme IDs to highlight in the gallery")
    parser.add_argument("--bytedance-preview", action="store_true", help="Also render a ByteDance preview")
    parser.add_argument("--cover", action="store_true", help="Also run the cover workflow")
    parser.add_argument("--skip-ai", action="store_true", help="Pass through to article_workflow.py")
    parser.add_argument("--skip-terminology", action="store_true", help="Pass through to article_workflow.py")
    parser.add_argument("--auto-accept-terminology", action="store_true", help="Pass through to article_workflow.py")
    parser.add_argument("--no-open", action="store_true", help="Pass through to article_workflow.py")
    parser.add_argument("--non-interactive", action="store_true", help="Pass through to article_workflow.py")
    parser.add_argument("--keep-existing", action="store_true", help="Pass through to article_workflow.py")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Stage inputs and write the handoff manifest without running article_workflow.py",
    )
    return parser.parse_args()


def load_records(archive_dir: Path) -> list[dict]:
    index_path = archive_dir / "index.json"
    if not index_path.exists():
        raise SystemExit(f"Missing archive index: {index_path}")
    records = json.loads(index_path.read_text(encoding="utf-8-sig"))
    if not isinstance(records, list):
        raise SystemExit(f"Archive index is not a list: {index_path}")
    return records


def resolve_record_path(raw_path: str, archive_dir: Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = archive_dir / path
    return path.expanduser().resolve()


def markdown_path_for(record: dict, archive_dir: Path) -> Path | None:
    raw_markdown = str(record.get("markdown_path", "")).strip()
    if raw_markdown:
        candidate = resolve_record_path(raw_markdown, archive_dir)
        if candidate.exists():
            return candidate

    raw_article_dir = str(record.get("article_dir", "")).strip()
    if raw_article_dir:
        candidate = resolve_record_path(raw_article_dir, archive_dir) / "article.md"
        if candidate.exists():
            return candidate
    return None


def record_matches(record: dict, markdown_path: Path, selectors: list[str]) -> bool:
    if not selectors:
        return True
    article_dir = markdown_path.parent.name.lower()
    markdown_stem = markdown_path.stem.lower()
    values = {
        str(record.get("seq", "")).lower(),
        str(record.get("title", "")).lower(),
        article_dir,
        markdown_stem,
    }
    return any(selector.lower() in values for selector in selectors)


def selected_records(records: list[dict], archive_dir: Path, selectors: list[str]) -> list[tuple[dict, Path]]:
    selected: list[tuple[dict, Path]] = []
    for record in records:
        if record.get("status") != "ok":
            continue
        markdown_path = markdown_path_for(record, archive_dir)
        if not markdown_path:
            continue
        if record_matches(record, markdown_path, selectors):
            selected.append((record, markdown_path))
    return selected


def safe_replace_dir(target: Path) -> None:
    target = target.resolve()
    parent = target.parent.resolve()
    if parent == target or parent.anchor == str(target):
        raise SystemExit(f"Refusing to replace unsafe stage directory: {target}")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)


def stage_article(record: dict, markdown_path: Path, stage_root: Path) -> dict:
    article_key = markdown_path.parent.name
    stage_dir = stage_root / article_key
    safe_replace_dir(stage_dir)

    staged_markdown = stage_dir / f"{article_key}.md"
    shutil.copy2(markdown_path, staged_markdown)

    images_dir = markdown_path.parent / "images"
    staged_images = stage_dir / "images"
    if images_dir.exists():
        shutil.copytree(images_dir, staged_images)

    meta_path = markdown_path.parent / "meta.json"
    staged_meta = stage_dir / "meta.json"
    if meta_path.exists():
        shutil.copy2(meta_path, staged_meta)

    return {
        "seq": record.get("seq"),
        "title": record.get("title", ""),
        "source_url": record.get("source_url", ""),
        "archive_article_dir": str(markdown_path.parent),
        "archive_markdown": str(markdown_path),
        "staged_dir": str(stage_dir),
        "staged_markdown": str(staged_markdown),
        "staged_images_dir": str(staged_images) if staged_images.exists() else None,
        "staged_meta": str(staged_meta) if staged_meta.exists() else None,
    }


def build_workflow_command(args: argparse.Namespace, staged_markdown: Path, workflow_output_root: Path) -> list[str]:
    cmd = [
        sys.executable,
        str(FORMAT_WORKFLOW),
        "--input",
        str(staged_markdown),
        "--output-root",
        str(workflow_output_root),
    ]
    if args.theme:
        cmd.extend(["--theme", args.theme])
    if args.recommend is not None:
        cmd.extend(["--recommend", *args.recommend])
    for flag_name, cli_flag in [
        ("bytedance_preview", "--bytedance-preview"),
        ("cover", "--cover"),
        ("skip_ai", "--skip-ai"),
        ("skip_terminology", "--skip-terminology"),
        ("auto_accept_terminology", "--auto-accept-terminology"),
        ("no_open", "--no-open"),
        ("non_interactive", "--non-interactive"),
        ("keep_existing", "--keep-existing"),
    ]:
        if getattr(args, flag_name):
            cmd.append(cli_flag)
    return cmd


def run_command(cmd: list[str]) -> int:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    print("Running:", " ".join(f'"{part}"' if " " in part else part for part in cmd))
    return subprocess.run(cmd, env=env).returncode


def write_manifest(stage_root: Path, payload: dict) -> Path:
    manifest_path = stage_root / "reformat-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def main() -> int:
    args = parse_args()
    archive_dir = Path(args.archive_dir).expanduser().resolve()
    if not archive_dir.exists():
        raise SystemExit(f"Archive directory does not exist: {archive_dir}")
    if not FORMAT_WORKFLOW.exists():
        raise SystemExit(f"Formatter workflow script does not exist: {FORMAT_WORKFLOW}")

    stage_root = Path(args.stage_root).expanduser().resolve()
    workflow_output_root = Path(args.workflow_output_root).expanduser().resolve()

    records = load_records(archive_dir)
    articles = selected_records(records, archive_dir, args.article)
    if not articles:
        raise SystemExit("No archived article Markdown matched the requested selector(s).")

    handoff_items = []
    exit_code = 0
    for record, markdown_path in articles:
        item = stage_article(record, markdown_path, stage_root)
        cmd = build_workflow_command(args, Path(item["staged_markdown"]), workflow_output_root)
        item["workflow_command"] = cmd
        item["workflow_output_root"] = str(workflow_output_root)
        item["workflow_slug"] = Path(item["staged_markdown"]).stem
        item["workflow_root"] = str(workflow_output_root / item["workflow_slug"])
        if args.dry_run:
            item["workflow_status"] = "dry-run"
        else:
            code = run_command(cmd)
            item["workflow_status"] = "ok" if code == 0 else "failed"
            item["workflow_exit_code"] = code
            if code != 0 and exit_code == 0:
                exit_code = code
        handoff_items.append(item)

    manifest = {
        "archive_dir": str(archive_dir),
        "stage_root": str(stage_root),
        "workflow_script": str(FORMAT_WORKFLOW),
        "workflow_output_root": str(workflow_output_root),
        "article_count": len(handoff_items),
        "dry_run": args.dry_run,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "articles": handoff_items,
    }
    manifest_path = write_manifest(stage_root, manifest)

    print(f"Prepared {len(handoff_items)} archived article(s) for reformatting.")
    print(f"- Stage root: {stage_root}")
    print(f"- Workflow output root: {workflow_output_root}")
    print(f"- Handoff manifest: {manifest_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
