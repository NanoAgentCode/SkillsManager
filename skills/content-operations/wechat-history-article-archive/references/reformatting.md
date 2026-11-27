# Reformatting Archived Articles

Use the bridge when the user requests migration, WeChat formatting or preparation for republishing. It stages each selected `article.md` with its sibling `images/` and `meta.json` and delegates rendering to [wechat-format](../../wechat-format/SKILL.md). Consult the formatter for content mode, theme, cover, and draft options. Publication requires its own explicit request.

## Select and stage

- Reuse explicit selections. If several articles qualify and the request leaves the scope unclear, ask which to use before running the bridge. Repeat `--article` for individual selections by sequence number, title, article directory name, or Markdown stem. Omitting it selects all successful entries with Markdown.
- Pass a fresh `--stage-root` or check the existing selected subdirectories and manifest before reuse. The bridge replaces staged article subdirectories and rewrites `reformat-manifest.json`. For existing formatter results, choose a fresh `--workflow-output-root` unless the user has approved their replacement.
- `--dry-run` stages inputs and writes the manifest while skipping the formatter. Use a fresh stage root for a staging test. If exact content preservation is requested, stage first, then use the staged inputs with the formatter's `--preserve-content` mode.

Run from the business project root using the bridge's installed path. These commands assume the current project also contains the skill checkout.

```powershell
.\scripts\run-python.ps1 .\skills\content-operations\wechat-history-article-archive\scripts\reformat_archived_articles.py --archive-dir .\output\wechat-history-article-archive\archive --article 1 --theme apple-code --skip-ai --no-open --non-interactive
```

```bash
python3 ./skills/content-operations/wechat-history-article-archive/scripts/reformat_archived_articles.py \
  --archive-dir ./output/wechat-history-article-archive/archive \
  --article 1 --theme apple-code --skip-ai --no-open --non-interactive
```

## Check the handoff

Inside the same business project, the default stage root is `output/wechat-history-article-archive/reformat-inputs/` and the default formatter root is `output/wechat-format/article-workflows/`. Verify the Markdown, metadata, and any images listed in `reformat-manifest.json`. After rendering, report the formatter's `manifest.json` and final `preview.html`, `article.html`, plus any produced cover or ByteDance preview.
