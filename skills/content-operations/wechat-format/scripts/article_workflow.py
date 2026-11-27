#!/usr/bin/env python3
"""Run the repo-local WeChat article workflow end to end."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config_loader import load_config


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
WECHAT_COVER_DIR = SKILL_DIR.parent / "wechat-cover"
DEFAULT_RECOMMEND = ["apple-code", "github", "bytedance", "sspai"]
LOCAL_IMAGE_SUFFIXES = {".avif", ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
POLISH_STYLES = {
    "professional": "专业文章",
    "popular-science": "科普文章",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate structured/enhanced markdown, open the gallery flow, and save final WeChat outputs."
    )
    parser.add_argument("--input", "-i", required=True, help="Input Markdown article path")
    parser.add_argument(
        "--output-root",
        "-o",
        default="output/wechat-format/article-workflows",
        help="Root directory for workflow artifacts, relative to the calling project's working directory",
    )
    parser.add_argument(
        "--theme",
        help="Final theme ID. If omitted, the script opens the gallery and then prompts for the chosen theme.",
    )
    parser.add_argument(
        "--recommend",
        nargs="*",
        default=DEFAULT_RECOMMEND,
        help="Recommended theme IDs to highlight in the gallery",
    )
    parser.add_argument(
        "--bytedance-preview",
        action="store_true",
        help="Also render a ByteDance-themed preview artifact",
    )
    parser.add_argument(
        "--cover",
        action="store_true",
        help="Also generate a cover artifact with wechat-cover/config.json",
    )
    parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="Skip AI structured/enhanced generation and copy the source forward unchanged",
    )
    parser.add_argument(
        "--preserve-content",
        action="store_true",
        help="Treat the input as final approved Markdown and preserve its wording, structure, image links, and captions",
    )
    parser.add_argument(
        "--skip-terminology",
        action="store_true",
        help="Skip the terminology-polish step and start from the source article directly",
    )
    parser.add_argument(
        "--polish-style",
        choices=POLISH_STYLES,
        help="Required writing style for AI polishing: professional or popular-science. No default is inferred.",
    )
    parser.add_argument(
        "--auto-accept-terminology",
        action="store_true",
        help="Do not pause for manual confirmation after terminology polishing",
    )
    parser.add_argument(
        "--structured-input",
        help="Use an existing structured Markdown file instead of generating it",
    )
    parser.add_argument(
        "--enhanced-input",
        help="Use an existing enhanced Markdown file instead of generating it",
    )
    parser.add_argument(
        "--source-notes",
        help="Source/claim notes from technical-source-to-public-article to archive with the workflow",
    )
    parser.add_argument(
        "--visual-plan",
        help="Visual plan from technical-article-visual-director to archive with the workflow",
    )
    parser.add_argument(
        "--assets-dir",
        action="append",
        default=[],
        help="Additional directory used to resolve local Markdown image assets; may be repeated",
    )
    parser.add_argument(
        "--strict-assets",
        action="store_true",
        help="Fail before rendering when a local Markdown image cannot be resolved",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not auto-open gallery/final preview browser windows",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Fail instead of prompting for a theme when --theme is omitted",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Reuse an existing workflow directory instead of archiving it first",
    )
    return parser.parse_args()


def prompt_for_polish_style() -> str:
    prompt = (
        "Choose the article polishing style (no default):\n"
        "1. professional - 专业文章：保留专业深度与术语，表达严谨克制\n"
        "2. popular-science - 科普文章：降低理解门槛，解释必要术语\n"
        "> "
    )
    aliases = {
        "1": "professional",
        "professional": "professional",
        "专业": "professional",
        "专业文章": "professional",
        "2": "popular-science",
        "popular-science": "popular-science",
        "科普": "popular-science",
        "科普文章": "popular-science",
    }
    while True:
        choice = input(prompt).strip().lower()
        selected = aliases.get(choice)
        if selected:
            return selected
        print("A polishing style is required. Enter 1/professional or 2/popular-science.")


def resolve_polish_style(args: argparse.Namespace) -> str | None:
    needs_polishing = not (args.skip_ai or args.preserve_content or args.skip_terminology)
    if not needs_polishing:
        return None
    if args.polish_style:
        return args.polish_style
    if args.non_interactive:
        raise SystemExit(
            "Article polishing style is required. Pass --polish-style professional or "
            "--polish-style popular-science. No default is used."
        )
    return prompt_for_polish_style()


def slugify(name: str) -> str:
    value = re.sub(r"[^\w\-]+", "-", name, flags=re.UNICODE).strip("-_")
    value = re.sub(r"-{2,}", "-", value)
    return value or "article"


def extract_title(content: str, fallback: str) -> str:
    fm = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if fm:
        for line in fm.group(1).splitlines():
            if line.startswith("title:"):
                return line.split(":", 1)[1].strip().strip('"').strip("'")
    h1 = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if h1:
        return h1.group(1).strip()
    return fallback


def strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    match = re.match(r"^```(?:markdown|md)?\s*(.*?)\s*```$", cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip() + "\n"
    return cleaned + ("\n" if not cleaned.endswith("\n") else "")


def archive_existing_dir(target: Path) -> None:
    if not target.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = target.with_name(f"{target.name}-backup-{stamp}")
    shutil.move(str(target), str(backup))
    print(f"Archived previous workflow to: {backup}")


def ensure_clean_dir(target: Path, keep_existing: bool) -> None:
    if target.exists() and not keep_existing:
        archive_existing_dir(target)
    target.mkdir(parents=True, exist_ok=True)


def require_ai_config(config: dict) -> dict:
    ai_cfg = config.get("ai", {})
    url = str(ai_cfg.get("url", "")).strip()
    key = str(ai_cfg.get("api_key", "")).strip() or os.environ.get("OPENROUTER_API_KEY", "").strip()
    model = str(ai_cfg.get("model", "")).strip()
    if not url or not key or not model:
        raise SystemExit(
            "Missing AI config for structured/enhanced generation. Fill skills/content-operations/wechat-format/config.json -> ai "
            "or rerun with --skip-ai / --structured-input / --enhanced-input."
        )
    return {"url": url.rstrip("/"), "key": key, "model": model}


def call_chat_completion(ai_config: dict, system_prompt: str, user_prompt: str) -> str:
    try:
        import requests
    except ModuleNotFoundError:
        print("Missing dependency: requests")
        print(f"Install it with: {sys.executable} -m pip install requests")
        print(f"Or run: {sys.executable} {SCRIPT_DIR / 'check_dependencies.py'} --install")
        sys.exit(1)

    response = requests.post(
        f"{ai_config['url']}/chat/completions",
        headers={
            "Authorization": f"Bearer {ai_config['key']}",
            "Content-Type": "application/json",
        },
        json={
            "model": ai_config["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 8000,
        },
        timeout=180,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("AI response was empty")
    return strip_code_fences(content)


def build_structure_prompts(title: str, content: str) -> tuple[str, str]:
    system_prompt = (
        "You convert Chinese technical or long-form Markdown into a more structured Markdown draft. "
        "Preserve claims, wording, links, and code blocks. Add headings, paragraph breaks, lists, and very light emphasis only. "
        "Do not invent facts. Return Markdown only."
    )
    user_prompt = f"""Article title: {title}

Task:
1. Keep the article's meaning and wording stable.
2. If the Markdown is under-structured, add `##` section headings based on the article's real topic shifts.
3. Split long paragraphs where it improves readability.
4. Convert obvious enumerations into Markdown lists.
5. Keep code blocks, links, quotes, and technical terms intact.
6. Do not add marketing language or extra explanation.

Return only the structured Markdown.

Source article:

{content}
"""
    return system_prompt, user_prompt


def build_terminology_prompts(title: str, content: str, polish_style: str) -> tuple[str, str]:
    if polish_style == "professional":
        audience_guidance = (
            "Write for readers with relevant domain knowledge. Preserve necessary technical depth and standard terminology. "
            "Prefer precise, concise, restrained professional expression; do not dilute concepts into vague everyday language."
        )
        style_task = (
            "Polish as a professional article: retain domain terminology and technical depth, while improving rigor, "
            "clarity, consistency, and sentence flow."
        )
    elif polish_style == "popular-science":
        audience_guidance = (
            "Write for interested non-specialists. Reduce avoidable jargon and briefly explain unavoidable technical terms in context. "
            "Prefer concrete, readable transitions, but do not add unsupported facts, examples, analogies, or conclusions."
        )
        style_task = (
            "Polish as a popular-science article: lower the reading barrier, clarify necessary terms, and improve readability "
            "without weakening factual accuracy or expanding the source."
        )
    else:
        raise ValueError(f"Unsupported polish style: {polish_style}")

    system_prompt = (
        "You polish Chinese technical articles when terminology accuracy matters. "
        "Preserve the author's meaning, keep Markdown structure usable, and check terms in context. "
        f"{audience_guidance} "
        "Return valid JSON only with keys: polished_markdown, terminology_changes, uncertain_terms. "
        "terminology_changes must be an array of objects with keys original, revised, reason. "
        "uncertain_terms must be an array of strings."
    )
    user_prompt = f"""Article title: {title}

Task:
1. {style_task}
2. Preserve headings, lists, links, code blocks, and the author's technical position.
3. Keep changes conservative and traceable.
4. Record every meaningful terminology or expression correction in terminology_changes.
5. If a term is still uncertain, add it to uncertain_terms instead of guessing.

Return JSON only. Do not wrap it in Markdown fences.

Source article:

{content}
"""
    return system_prompt, user_prompt


def build_enhancement_prompts(title: str, content: str) -> tuple[str, str]:
    system_prompt = (
        "You prepare Markdown for the local wechat-format renderer. "
        "Preserve the article's content while adding only presentation-friendly Markdown enhancements. "
        "You may add callouts, thematic separators, and fenced containers like `:::dialogue[...]` or `:::gallery[...]` only when clearly supported by the source. "
        "Return Markdown only."
    )
    user_prompt = f"""Article title: {title}

Task:
1. Keep the article text and technical meaning intact.
2. Add low-risk presentation structure for the local WeChat formatter:
   - callouts for explicit key takeaways, tips, or cautions
   - `:::dialogue[...]` for obvious interview/dialogue sections
   - `:::gallery[...]` only for obvious consecutive image groups
   - `---` between major sections when helpful
3. Keep edits conservative. If a container is not clearly justified, leave the text as normal Markdown.
4. Do not invent screenshots, captions, sections, claims, or examples.

Return only the enhanced Markdown.

Structured Markdown:

{content}
"""
    return system_prompt, user_prompt


def parse_terminology_payload(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = strip_code_fences(cleaned).strip()
    payload = json.loads(cleaned)
    polished = payload.get("polished_markdown", "")
    changes = payload.get("terminology_changes", [])
    uncertain = payload.get("uncertain_terms", [])
    if not isinstance(polished, str) or not polished.strip():
        raise RuntimeError("Terminology step returned empty polished_markdown")
    if not isinstance(changes, list):
        raise RuntimeError("Terminology step returned invalid terminology_changes")
    if not isinstance(uncertain, list):
        raise RuntimeError("Terminology step returned invalid uncertain_terms")
    normalized_changes = []
    for item in changes:
        if not isinstance(item, dict):
            continue
        original = str(item.get("original", "")).strip()
        revised = str(item.get("revised", "")).strip()
        reason = str(item.get("reason", "")).strip()
        if original or revised or reason:
            normalized_changes.append(
                {"original": original, "revised": revised, "reason": reason}
            )
    normalized_uncertain = [str(item).strip() for item in uncertain if str(item).strip()]
    return {
        "polished_markdown": polished.strip() + "\n",
        "terminology_changes": normalized_changes,
        "uncertain_terms": normalized_uncertain,
    }


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_terminology_table(path: Path, changes: list[dict]) -> None:
    lines = [
        "| Original term/expression | Revised term/expression | Reason |",
        "|---|---|---|",
    ]
    for item in changes:
        original = item.get("original", "").replace("\n", " ").strip()
        revised = item.get("revised", "").replace("\n", " ").strip()
        reason = item.get("reason", "").replace("\n", " ").strip()
        lines.append(f"| {original} | {revised} | {reason} |")
    write_text(path, "\n".join(lines) + "\n")


def write_uncertain_terms(path: Path, uncertain_terms: list[str]) -> None:
    if not uncertain_terms:
        return
    lines = ["## Uncertain Terms", ""]
    lines.extend(f"- {term}" for term in uncertain_terms)
    lines.append("")
    write_text(path, "\n".join(lines))


def write_console_text(text: str, *, is_error: bool = False) -> None:
    if not text:
        return
    stream = sys.stderr if is_error else sys.stdout
    try:
        stream.write(text)
        if not text.endswith("\n"):
            stream.write("\n")
    except UnicodeEncodeError:
        safe_text = text.encode(stream.encoding or "utf-8", errors="replace").decode(stream.encoding or "utf-8", errors="replace")
        stream.write(safe_text)
        if not safe_text.endswith("\n"):
            stream.write("\n")


def copy_source(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def require_file(value: str | None, label: str) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"{label} file does not exist: {path}")
    return path


def require_directories(values: list[str], label: str) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        path = Path(value).expanduser().resolve()
        if not path.is_dir():
            raise SystemExit(f"{label} directory does not exist: {path}")
        if path not in paths:
            paths.append(path)
    return paths


def _markdown_image_source(raw_value: str) -> str:
    value = raw_value.strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")].strip()
    title_match = re.match(r"^(.*?)(?:\s+[\"'].*[\"'])$", value)
    return title_match.group(1).strip() if title_match else value


def _resolve_local_asset(source: str, input_dir: Path, asset_roots: list[Path]) -> Path | None:
    if not source or source.startswith(("http://", "https://", "data:", "#")):
        return None
    source_path = Path(source).expanduser()
    if source_path.suffix.lower() not in LOCAL_IMAGE_SUFFIXES:
        return None

    candidates: list[Path] = []
    if source_path.is_absolute():
        candidates.append(source_path)
    else:
        candidates.append(input_dir / source_path)
        for root in asset_roots:
            candidates.extend((root / source_path, root / source_path.name))

    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            return resolved
    return None


def _staged_asset_name(source: Path, used_names: dict[str, Path]) -> str:
    name = source.name
    previous = used_names.get(name.casefold())
    if previous is None or previous == source:
        used_names[name.casefold()] = source
        return name

    index = 2
    while True:
        candidate = f"{source.stem}-{index}{source.suffix.lower()}"
        previous = used_names.get(candidate.casefold())
        if previous is None or previous == source:
            used_names[candidate.casefold()] = source
            return candidate
        index += 1


def stage_markdown_assets(
    content: str,
    input_path: Path,
    render_dir: Path,
    asset_roots: list[Path],
) -> tuple[str, list[dict[str, str]], list[str]]:
    """Copy local Markdown images next to the render input and rewrite their paths."""
    images_dir = render_dir / "images"
    staged_by_source: dict[Path, str] = {}
    used_names: dict[str, Path] = {}
    staged_assets: list[dict[str, str]] = []
    unresolved_assets: list[str] = []

    def replace_image(match: re.Match[str]) -> str:
        alt = match.group(1)
        raw_source = match.group(2)
        source_value = _markdown_image_source(raw_source)
        if source_value.startswith(("http://", "https://", "data:", "#")):
            return match.group(0)

        source_path = _resolve_local_asset(source_value, input_path.parent, asset_roots)
        if source_path is None:
            if source_value and source_value not in unresolved_assets:
                unresolved_assets.append(source_value)
            return match.group(0)

        staged_name = staged_by_source.get(source_path)
        if staged_name is None:
            staged_name = _staged_asset_name(source_path, used_names)
            destination = images_dir / staged_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination)
            staged_by_source[source_path] = staged_name
            staged_assets.append(
                {
                    "source": str(source_path),
                    "staged": str(destination),
                    "markdown_path": f"images/{staged_name}",
                }
            )
        return f"![{alt}](images/{staged_name})"

    rewritten = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_image, content)
    return rewritten, staged_assets, unresolved_assets


def enforce_asset_resolution(unresolved_assets: list[str], strict: bool) -> None:
    if strict and unresolved_assets:
        raise SystemExit(
            "Unresolved local Markdown assets: " + ", ".join(unresolved_assets)
        )


def run_subprocess(cmd: list[str], env: dict[str, str]) -> subprocess.CompletedProcess:
    print("Running:", " ".join(f'"{part}"' if " " in part else part for part in cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)
    if result.stdout:
        write_console_text(result.stdout.rstrip())
    if result.returncode != 0:
        if result.stderr:
            write_console_text(result.stderr.rstrip(), is_error=True)
        raise SystemExit(result.returncode)
    return result


def run_check_dependencies(env: dict[str, str]) -> None:
    run_subprocess([sys.executable, str(SCRIPT_DIR / "check_dependencies.py")], env)


def run_format(
    render_input: Path,
    output_root: Path,
    env: dict[str, str],
    *,
    gallery: bool = False,
    theme: str | None = None,
    recommend: list[str] | None = None,
    no_open: bool = False,
) -> Path:
    cmd = [sys.executable, str(SCRIPT_DIR / "format.py"), "--input", str(render_input), "--output", str(output_root)]
    if gallery:
        cmd.append("--gallery")
        if recommend:
            cmd.extend(["--recommend", *recommend])
    if theme:
        cmd.extend(["--theme", theme])
    if no_open:
        cmd.append("--no-open")
    run_subprocess(cmd, env)
    return output_root / render_input.stem


def available_themes() -> list[str]:
    return sorted(path.stem for path in (SKILL_DIR / "themes").glob("*.json"))


def prompt_for_theme(default_theme: str) -> str:
    theme_ids = available_themes()
    prompt = (
        "Gallery is ready. Enter the selected theme ID"
        f" [{default_theme}]. Available themes: {', '.join(theme_ids)}\n> "
    )
    choice = input(prompt).strip()
    return choice or default_theme


def prompt_for_terminology_confirmation(
    polished_path: Path,
    terminology_table_path: Path,
    uncertain_terms_path: Path | None,
) -> bool:
    print("\nTerminology review is ready:")
    print(f"- Polished Markdown: {polished_path}")
    print(f"- Terminology changes: {terminology_table_path}")
    if uncertain_terms_path and uncertain_terms_path.exists():
        print(f"- Uncertain terms: {uncertain_terms_path}")
    choice = input("Continue to structured/enhanced formatting? [Y/n]: ").strip().lower()
    return choice in ("", "y", "yes")


def build_cover_prompt(title: str, content: str) -> str:
    summary = summarize_article(content)
    body = (
        "请根据提供的内容创建一张吸引眼球的公众号封面图，遵循以下规范：\n\n"
        "视觉风格\n"
        "- Notion插画风格，比例为 2.35:1（公众号封面标准尺寸）\n"
        "- 色彩鲜明、对比强烈，确保在小尺寸预览时依然醒目\n"
        "- 风格统一，避免写实元素，保持整体手绘质感\n\n"
        "构图要求\n"
        "- 主视觉元素居中或偏左（右侧预留标题区域）\n"
        "- 添加 1-2 个简洁的卡通形象、图标或人物剪影，增强记忆点\n"
        "- 大量留白，突出核心信息，避免画面拥挤\n\n"
        "文字处理\n"
        "- 标题文字大而醒目，控制在 8 字以内\n"
        "- 可添加 1 行副标题或关键词标签\n"
        "- 字体风格与手绘插画协调统一\n\n"
        "吸引力法则\n"
        "- 使用悬念、数字、痛点等钩子元素激发点击欲望\n"
        "- 视觉元素夸张有反差\n"
        "- 色彩搭配参考爆款封面：橙黄、蓝紫、红黑等高对比组合\n\n"
        "语言\n"
        "- 除非另有说明，默认使用中文\n"
        "- 画面内所有可读文字必须使用简体中文，英文只能作为点缀出现\n\n"
        f"内容主题：{title}。一句话摘要：{summary}\n"
    )
    return f'---\naspect_ratio: "21:9"\nimage_size: "2K"\n---\n\n{body}'


def summarize_article(content: str, limit: int = 140) -> str:
    text = re.sub(r"^---\n.*?\n---\n*", "", content, flags=re.DOTALL)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[#>*`_\-\[\]]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit].rstrip(" ,，。") or "文章核心观点"


def run_cover_generation(prompt_path: Path, cover_path: Path, env: dict[str, str]) -> None:
    config_path = WECHAT_COVER_DIR / "config.json"
    if not config_path.exists():
        raise SystemExit(
            "Cover generation requested, but skills/content-operations/wechat-cover/config.json is missing."
        )
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "generate.py"),
        "--config",
        str(config_path),
        "--prompt-file",
        str(prompt_path),
        "--out",
        str(cover_path),
    ]
    run_subprocess(cmd, env)


def write_manifest(path: Path, payload: dict) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    args = parse_args()
    polish_style = resolve_polish_style(args)
    config = load_config(SKILL_DIR)

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file does not exist: {input_path}")
    source_notes_input = require_file(args.source_notes, "Source notes")
    visual_plan_input = require_file(args.visual_plan, "Visual plan")
    asset_roots = require_directories(args.assets_dir, "Asset root")
    structured_input = require_file(args.structured_input, "Structured input")
    enhanced_input = require_file(args.enhanced_input, "Enhanced input")
    preserve_content = args.skip_ai or args.preserve_content

    original_content = input_path.read_text(encoding="utf-8")
    article_slug = slugify(input_path.stem)
    title = extract_title(original_content, input_path.stem)

    workflow_root = Path(args.output_root).expanduser().resolve() / article_slug
    ensure_clean_dir(workflow_root, args.keep_existing)

    source_dir = workflow_root / "source"
    markdown_dir = workflow_root / "markdown"
    render_dir = workflow_root / "render"
    gallery_root = workflow_root / "gallery"
    selection_dir = workflow_root / "selection"
    final_root = workflow_root / "final"
    bytedance_root = workflow_root / "bytedance"
    cover_dir = workflow_root / "cover"
    upstream_dir = workflow_root / "upstream"

    source_copy = source_dir / input_path.name
    polished_path = markdown_dir / f"{article_slug}-polished.md"
    terminology_table_path = markdown_dir / f"{article_slug}-terminology-changes.md"
    uncertain_terms_path = markdown_dir / f"{article_slug}-uncertain-terms.md"
    structured_path = markdown_dir / f"{article_slug}-structured.md"
    enhanced_path = markdown_dir / f"{article_slug}-enhanced.md"
    render_input = render_dir / input_path.name
    manifest_path = workflow_root / "manifest.json"

    copy_source(input_path, source_copy)
    source_notes_copy = None
    visual_plan_copy = None
    if source_notes_input:
        source_notes_copy = upstream_dir / "source-notes.md"
        copy_source(source_notes_input, source_notes_copy)
    if visual_plan_input:
        visual_plan_copy = upstream_dir / "visual-plan.md"
        copy_source(visual_plan_input, visual_plan_copy)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    run_check_dependencies(env)

    terminology_changes: list[dict] = []
    uncertain_terms: list[str] = []

    if preserve_content or args.skip_terminology:
        polished_content = original_content
    else:
        ai_config = require_ai_config(config)
        system_prompt, user_prompt = build_terminology_prompts(title, original_content, polish_style)
        print(f"Generating {POLISH_STYLES[polish_style]} terminology-polished Markdown...")
        terminology_result = parse_terminology_payload(
            call_chat_completion(ai_config, system_prompt, user_prompt)
        )
        polished_content = terminology_result["polished_markdown"]
        terminology_changes = terminology_result["terminology_changes"]
        uncertain_terms = terminology_result["uncertain_terms"]
    write_text(polished_path, polished_content)
    write_terminology_table(terminology_table_path, terminology_changes)
    write_uncertain_terms(uncertain_terms_path, uncertain_terms)

    if not preserve_content and not args.skip_terminology and not args.auto_accept_terminology:
        if args.non_interactive:
            raise SystemExit(
                "Terminology confirmation is required. Re-run interactively, or pass "
                "--auto-accept-terminology / --skip-terminology."
            )
        accepted = prompt_for_terminology_confirmation(
            polished_path,
            terminology_table_path,
            uncertain_terms_path if uncertain_terms else None,
        )
        if not accepted:
            raise SystemExit(
                "Stopped after terminology review. Inspect or edit the generated files, then rerun "
                "with --structured-input / --enhanced-input or accept terminology next time."
            )

    if structured_input:
        structured_content = structured_input.read_text(encoding="utf-8")
    elif preserve_content:
        structured_content = polished_content
    else:
        ai_config = require_ai_config(config)
        system_prompt, user_prompt = build_structure_prompts(title, polished_content)
        print("Generating structured Markdown...")
        structured_content = call_chat_completion(ai_config, system_prompt, user_prompt)
    write_text(structured_path, structured_content)

    if enhanced_input:
        enhanced_content = enhanced_input.read_text(encoding="utf-8")
        render_source_path = enhanced_input
    elif preserve_content:
        enhanced_content = structured_content
        render_source_path = structured_input or input_path
    else:
        ai_config = require_ai_config(config)
        system_prompt, user_prompt = build_enhancement_prompts(title, structured_content)
        print("Generating enhanced Markdown...")
        enhanced_content = call_chat_completion(ai_config, system_prompt, user_prompt)
        render_source_path = structured_input or input_path
    write_text(enhanced_path, enhanced_content)
    render_content, staged_assets, unresolved_assets = stage_markdown_assets(
        enhanced_content,
        render_source_path,
        render_dir,
        asset_roots,
    )
    enforce_asset_resolution(unresolved_assets, args.strict_assets)
    write_text(render_input, render_content)

    gallery_dir = run_format(
        render_input,
        gallery_root,
        env,
        gallery=True,
        recommend=args.recommend,
        no_open=args.no_open,
    )

    selected_theme = args.theme
    if not selected_theme:
        if args.non_interactive:
            raise SystemExit("No --theme provided and --non-interactive was set.")
        default_theme = "newspaper"
        gallery_selection = gallery_dir / "selected-theme.txt"
        if gallery_selection.exists():
            saved_theme = gallery_selection.read_text(encoding="utf-8").strip()
            if saved_theme:
                default_theme = saved_theme
        selected_theme = prompt_for_theme(default_theme)

    selection_dir.mkdir(parents=True, exist_ok=True)
    write_text(selection_dir / "selected-theme.txt", selected_theme + "\n")

    final_dir = run_format(
        render_input,
        final_root / selected_theme,
        env,
        theme=selected_theme,
        no_open=args.no_open,
    )

    bytedance_dir = None
    if args.bytedance_preview:
        bytedance_dir = run_format(
            render_input,
            bytedance_root,
            env,
            theme="bytedance",
            no_open=args.no_open,
        )

    cover_path = None
    prompt_path = None
    if args.cover:
        cover_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = cover_dir / "prompt.md"
        cover_path = cover_dir / "cover.jpg"
        write_text(prompt_path, build_cover_prompt(title, enhanced_content))
        run_cover_generation(prompt_path, cover_path, env)

    manifest = {
        "title": title,
        "input": str(input_path),
        "preserve_content": preserve_content,
        "polish_style": polish_style,
        "workflow_root": str(workflow_root),
        "source_copy": str(source_copy),
        "source_notes_input": str(source_notes_input) if source_notes_input else None,
        "source_notes": str(source_notes_copy) if source_notes_copy else None,
        "visual_plan_input": str(visual_plan_input) if visual_plan_input else None,
        "visual_plan": str(visual_plan_copy) if visual_plan_copy else None,
        "asset_roots": [str(path) for path in asset_roots],
        "strict_assets": args.strict_assets,
        "staged_assets": staged_assets,
        "unresolved_assets": unresolved_assets,
        "polished_markdown": str(polished_path),
        "terminology_changes": str(terminology_table_path),
        "uncertain_terms": str(uncertain_terms_path) if uncertain_terms else None,
        "structured_markdown": str(structured_path),
        "enhanced_markdown": str(enhanced_path),
        "render_input": str(render_input),
        "gallery_dir": str(gallery_dir),
        "gallery_html": str(gallery_dir / "gallery.html"),
        "selected_theme": selected_theme,
        "selection_file": str(selection_dir / "selected-theme.txt"),
        "final_dir": str(final_dir),
        "final_preview": str(final_dir / "preview.html"),
        "final_article": str(final_dir / "article.html"),
        "bytedance_dir": str(bytedance_dir) if bytedance_dir else None,
        "bytedance_preview": str(bytedance_dir / "preview.html") if bytedance_dir else None,
        "cover_prompt": str(prompt_path) if prompt_path else None,
        "cover_path": str(cover_path) if cover_path else None,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_manifest(manifest_path, manifest)

    print("\nWorkflow complete")
    print(f"- Workflow root: {workflow_root}")
    if source_notes_copy:
        print(f"- Source notes: {source_notes_copy}")
    if visual_plan_copy:
        print(f"- Visual plan: {visual_plan_copy}")
    if staged_assets:
        print(f"- Staged local assets: {len(staged_assets)}")
    if unresolved_assets:
        print(f"- Unresolved local assets: {', '.join(unresolved_assets)}")
    print(f"- Polished Markdown: {polished_path}")
    print(f"- Terminology changes: {terminology_table_path}")
    if uncertain_terms:
        print(f"- Uncertain terms: {uncertain_terms_path}")
    print(f"- Structured Markdown: {structured_path}")
    print(f"- Enhanced Markdown: {enhanced_path}")
    print(f"- Gallery: {gallery_dir / 'gallery.html'}")
    print(f"- Final theme: {selected_theme}")
    print(f"- Final preview: {final_dir / 'preview.html'}")
    if bytedance_dir:
        print(f"- ByteDance preview: {bytedance_dir / 'preview.html'}")
    if cover_path:
        print(f"- Cover: {cover_path}")
    print(f"- Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
