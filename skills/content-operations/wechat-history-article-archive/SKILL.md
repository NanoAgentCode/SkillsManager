---
name: wechat-history-article-archive
description: Use when backing up, migrating, or reformatting historical WeChat articles from an owned or authorized account. Archives lawful article URLs as Markdown, metadata, and local images, with an optional wechat-format handoff; excludes private-API history scraping.
---

# WeChat History Article Archive

Archive historical mass-send articles from an account the user owns or is authorized to operate. Use links copied or exported from the official account's sent history, a supplied export, or pasted `mp.weixin.qq.com/s?...` links. The permanent-material API covers a different collection.

Use `<business-project>/output/wechat-history-article-archive/` for the URL list, archive, and staging outputs unless the user provides a destination.

## Choose the operation

1. **Archive links.** Use a supplied URL list directly after checking its scope. For mixed text, use `scripts/extract_mp_urls.py` first to normalize and deduplicate the list. If browser collection from the admin UI is needed, use only an available, authorized signed-in session. If account authority or the article range is unclear, ask for the missing scope or an authorized export. Handle login, CAPTCHA, and risk-control blocks by using a user-provided export or URL list.
2. **Convert an existing archive.** Use `scripts/convert_archive_to_markdown.py` with its existing index and retained HTML. It updates Markdown, metadata and indexes. Keep HTML by default and pass `--delete-html` only when the user explicitly approves deletion after successful conversion.
3. **Prepare selected archived articles for republishing.** Read [reformatting.md](references/reformatting.md). Reuse the archived Markdown and images through the existing formatter bridge. Apply a confirmed selection and theme or send the relevant choices to the formatter.

## Archive commands

Use the installed `wechat-archive` command with Python 3.10 or newer. The first command is for an approved installation from the repository root.

```text
python -m pip install ./skills/content-operations/wechat-history-article-archive
wechat-archive extract --input history-source.txt --output output/wechat-history-article-archive/history-urls.txt
wechat-archive fetch --input output/wechat-history-article-archive/history-urls.txt --output-dir output/wechat-history-article-archive/archive
wechat-archive export --archive-dir output/wechat-history-article-archive/archive
```

Run the installed command from the business project root. The bundled-script examples below use the Skills Manager checkout as the current project. From another project, use absolute paths to the scripts and keep output arguments relative to that project or absolute.

```powershell
$archiveSkill = '.\skills\content-operations\wechat-history-article-archive'
$archiveOutput = '.\output\wechat-history-article-archive'
.\scripts\run-python.ps1 "$archiveSkill\scripts\extract_mp_urls.py" --input .\history-source.txt --output "$archiveOutput\history-urls.txt"
.\scripts\run-python.ps1 "$archiveSkill\scripts\archive_article_urls.py" --input "$archiveOutput\history-urls.txt" --output-dir "$archiveOutput\archive"
.\scripts\run-python.ps1 "$archiveSkill\scripts\convert_archive_to_markdown.py" --archive-dir "$archiveOutput\archive"
```

```bash
archive_skill=./skills/content-operations/wechat-history-article-archive
archive_output=./output/wechat-history-article-archive
python3 "$archive_skill/scripts/extract_mp_urls.py" --input ./history-source.txt --output "$archive_output/history-urls.txt"
python3 "$archive_skill/scripts/archive_article_urls.py" --input "$archive_output/history-urls.txt" --output-dir "$archive_output/archive"
python3 "$archive_skill/scripts/convert_archive_to_markdown.py" --archive-dir "$archive_output/archive"
```

Run conversion only for archives with retained `article.html` files. Fetch already writes Markdown. Use `--keep-html` when intermediate HTML is part of the requested archive. When a fetch output path already contains an archive, choose a fresh path unless the user authorizes reusing it and replacing the indexes. Keep real exports, session credentials, and generated files in local ignored paths.

## Verify and report

Check `index.json` and `index.csv`, and verify the `articles/<slug>/article.md`, `meta.json` and any referenced images for successful entries. Report recognized URLs, successes, failures, and the archive directory. Keep failed links and recorded errors for follow-up. A page needs a valid article body with text or images to count as successful. Slow requests for transient failures and use authorized sources for blocked pages.
