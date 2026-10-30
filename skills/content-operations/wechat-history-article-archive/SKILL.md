---
name: wechat-history-article-archive
description: Use when backing up, migrating, or reformatting historical WeChat articles from an owned or authorized account. Archives lawful article URLs as Markdown, metadata, and local images, with an optional wechat-format handoff; excludes private-API history scraping.
---

# wechat-history-article-archive

Back up historical mass-send articles for a self-owned or explicitly authorized WeChat Official Account. Start from lawful article URLs visible/exportable to the account operator, then archive public article pages as local Markdown, metadata, indexes, and images. When the user wants migration, reformatting, or republishing, hand archived Markdown to `../wechat-format/scripts/article_workflow.py` through the bundled bridge script.

## Scope

- Only process articles for accounts the user owns or is explicitly authorized to operate.
- Prefer URL lists copied or exported from the WeChat Official Account admin UI.
- Do not ask for `AppID` / `AppSecret` for history backup. The normal input is an article URL list, not the permanent-material API.
- Do not describe permanent material export as a full historical mass-send export.
- Do not bypass captchas, risk controls, login limits, private APIs, or access restrictions.

## Bundled Scripts

- `scripts/extract_mp_urls.py`
  - Extract and deduplicate `mp.weixin.qq.com/s?...` article URLs from text, HTML, CSV fragments, clipboard dumps, or notes.
  - Output a clean one-URL-per-line list.
- `scripts/archive_article_urls.py`
  - Read a URL list and batch-fetch public article pages.
  - Save Markdown, metadata JSON, index CSV/JSON, and local images by default.
  - Keep intermediate `article.html` only when `--keep-html` is passed.
- `scripts/convert_archive_to_markdown.py`
  - Convert archived `article.html` files into `article.md`.
  - Download article images into each article's `images/` folder.
  - Optionally delete legacy `article.html` with `--delete-html`.
- `scripts/reformat_archived_articles.py`
  - Stage archived `articles/<slug>/article.md`, sibling `images/`, and `meta.json` into formatter-ready folders.
  - Call `../wechat-format/scripts/article_workflow.py` for one or more archived articles.
  - Write `output/wechat-history-article-archive/reformat-inputs/reformat-manifest.json` with archive paths, staged inputs, formatter commands, and workflow output roots.

## Workflow

### 1. Confirm the Source

Use one of these lawful sources:

1. Article links manually copied from the account's "sent" history in the Official Account admin UI.
2. A backend export, spreadsheet, page source, or pasted text that contains article links.
3. Browser automation only when the current environment explicitly provides browser control and the user is already logged in to their own authorized account.

If reliable browser automation is unavailable, ask the user for a URL list or exported text and continue from there.

### 2. Normalize the URL List

PowerShell:

```powershell
$Python = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $Python `
  .\skills\content-operations\wechat-history-article-archive\scripts\extract_mp_urls.py `
  --input .\history-source.txt `
  --output .\output\wechat-history-article-archive\history-urls.txt
```

Portable shell:

```bash
python3 ./skills/content-operations/wechat-history-article-archive/scripts/extract_mp_urls.py \
  --input ./history-source.txt \
  --output ./output/wechat-history-article-archive/history-urls.txt
```

### 3. Archive the Article Pages

PowerShell:

```powershell
& $Python `
  .\skills\content-operations\wechat-history-article-archive\scripts\archive_article_urls.py `
  --input .\output\wechat-history-article-archive\history-urls.txt `
  --output-dir .\output\wechat-history-article-archive\archive
```

Portable shell:

```bash
python3 ./skills/content-operations/wechat-history-article-archive/scripts/archive_article_urls.py \
  --input ./output/wechat-history-article-archive/history-urls.txt \
  --output-dir ./output/wechat-history-article-archive/archive
```

Default archive output:

```text
index.json
index.csv
articles/<slug>/article.md
articles/<slug>/meta.json
articles/<slug>/images/*
```

If the archive already contains `article.html` files, convert them afterward:

```powershell
& $Python `
  .\skills\content-operations\wechat-history-article-archive\scripts\convert_archive_to_markdown.py `
  --archive-dir .\output\wechat-history-article-archive\archive `
  --delete-html
```

### 4. Review Failures

For failed links:

- Check whether the URL is expired, deleted, malformed, or requires login.
- A response without a valid `#js_content` body or without text/images is recorded as a failure, not an empty successful archive. Keep the URL and error from `index.json` for follow-up.
- Reduce request speed if there are transient failures.
- Do not try to bypass verification, risk control, login restrictions, or non-public interfaces.

### 5. Reformat Archived Articles for Republishing

When the user wants reformatting, migration, or republishing preparation, prefer the bridge script instead of manually copying archive files into `wechat-format`.

PowerShell:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
& $Python `
  .\skills\content-operations\wechat-history-article-archive\scripts\reformat_archived_articles.py `
  --archive-dir .\output\wechat-history-article-archive\archive `
  --article 1 `
  --theme apple-code `
  --skip-ai `
  --no-open `
  --non-interactive
```

Portable shell:

```bash
PYTHONIOENCODING=utf-8 python3 ./skills/content-operations/wechat-history-article-archive/scripts/reformat_archived_articles.py \
  --archive-dir ./output/wechat-history-article-archive/archive \
  --article 1 \
  --theme apple-code \
  --skip-ai \
  --no-open \
  --non-interactive
```

Selection rules:

- Omit `--article` to process every successful archived article.
- Repeat `--article` for multiple items.
- A selector can match `seq`, title, article directory name, or Markdown filename stem.
- Use `--dry-run` to validate staging paths and formatter command construction without running the formatter.

Default handoff output:

```text
output/wechat-history-article-archive/reformat-inputs/
  <archive-article-slug>/
    <archive-article-slug>.md
    images/
    meta.json
  reformat-manifest.json

output/wechat-format/article-workflows/<archive-article-slug>/
  source/
  markdown/
  render/
  gallery/
  selection/
  final/<theme>/
  bytedance/
  cover/
  manifest.json
```

Report `reformat-manifest.json`, formatter `manifest.json`, final `preview.html`, final `article.html`, and optional cover/ByteDance preview paths.

## Configuration

No `config.json` is required for archive-only runs. If fixed local defaults are needed, create a local `config.json` beside this skill and use `config.example.json` as the safe example. Do not commit real local config values.

The reformat bridge delegates to `wechat-format/scripts/article_workflow.py`. Read `../wechat-format/SKILL.md` when the user asks for theme selection, AI polishing, cover generation, or draft publishing details.

## Output Expectations

When finishing an archive task, report:

- Number of URLs recognized.
- Number of successful and failed archives.
- Archive directory.
- Whether the permanent-material API boundary is relevant.
- If reformatting was requested: staged handoff directory, `reformat-manifest.json`, formatter workflow root, final preview/article HTML, and any cover/ByteDance preview artifacts.

## Safety Rules

- Only archive articles from self-owned or explicitly authorized accounts.
- Do not scrape unauthorized third-party account history.
- Do not use private APIs or bypass access controls.
- Do not commit cookies, tokens, real exports, generated outputs, or local `config.json`.
- Use browser automation only when the current environment actually exposes that capability and the user is already logged in to their authorized account.
