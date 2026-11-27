# Repository Operations

This guide contains shared installation, invocation, validation, output, and security conventions. Skill-specific workflows remain in each `SKILL.md`.

## Use A Skill

1. Choose the closest business scenario in `docs/skill-index.md`.
2. Read the selected `SKILL.md` completely.
3. Use bundled scripts for repeatable operations.
4. Write generated artifacts under the business project's `output/<skill-name>/`. Use an explicit user-supplied destination when present.

Example:

```text
Read AGENTS.md, then read skills/content-operations/wechat-format/SKILL.md, and format this article for WeChat.
```

## Windows Python Launcher

Do not assume `python` or `py` is available on `PATH`. From the repository root, use:

```powershell
.\scripts\run-python.ps1 <script-path> [arguments]
```

The launcher checks configured runtimes, repository environments, the Windows registry, and common installation paths. It reports a clear prerequisite error when no interpreter is available.

## Standalone Commands

Use Python 3.10 or later. Install from the skill checkout and run the installed commands from the business project root. For example:

```text
python -m pip install ./skills/engineering-operations/python-offline-dependency-packager
offline-deps versions --package requests
offline-deps bundle --package requests --version 2.32.5 --python-version 3.11
python -m pip install ./skills/content-operations/official-format-pro
official-format convert --title "公文标题" --input content.md --output result.docx
python -m pip install ./skills/knowledge-visualization/drawio-skill
depgraph generate ./src --language python --no-reduce -o output/drawio-skill/dependencies.drawio
depgraph validate output/drawio-skill/dependencies.drawio
python -m pip install ./skills/content-operations/wechat-history-article-archive
wechat-archive extract --input history-source.txt --output output/wechat-history-article-archive/history-urls.txt
wechat-archive fetch --input output/wechat-history-article-archive/history-urls.txt --output-dir output/wechat-history-article-archive/archive
wechat-archive export --archive-dir output/wechat-history-article-archive/archive
python -m pip install ./skills/content-operations/video-transcriber
media-subtitle-to-md captions.srt --output output/video-transcriber/transcript.md
media-extract-audio video.mp4 --output-dir output/video-transcriber
python -m pip install ./skills/market-intelligence/us-sector-index-impact-report
sector-report-render --input report-data.json --output output/us-sector-index-impact-report/report.html
```

The knowledge tools run from a checkout with PowerShell 7. Rendering also requires `markmap` on PATH.

```text
pwsh -File scripts/knowledge-tools.ps1 --help
pwsh -File scripts/knowledge-tools.ps1 mindmap-render -InputMarkdown outline.md -OutputHtml mindmap.html
pwsh -File scripts/knowledge-tools.ps1 mindmap-publish -SourceHtml mindmap.html -StaticRoot ./staging -PublicBaseUrl https://example.test -PathPrefix /maps -Slug demo
pwsh -File scripts/knowledge-tools.ps1 vault-search -VaultPath ./vault -Query "RAG,vector"
pwsh -File scripts/knowledge-tools.ps1 vault-reindex -VaultPath ./vault
pwsh -File scripts/knowledge-tools.ps1 vault-audit -VaultPath ./vault -Json
```

Run WeChat article rendering or draft upload from the repository checkout:

```text
python scripts/wechat-tools.py render --input article.md --theme apple-code --preserve-content --no-open --non-interactive
python scripts/wechat-tools.py draft --dir ./rendered-article --cover ./cover.png
```

Use the final directory containing `article.html` for `--dir`. Add `--dry-run` to check the article, local image files, and cover offline. Remote image URLs are counted without fetching them. The `--input` form also renders Markdown locally and requires `markdown`.

To retain the former image-upload behavior of `--dry-run`, switch to `--upload-only`. This uploads body images and the cover to WeChat and stops before draft creation. Omit both flags to submit the draft. Both online modes require `requests` and local WeChat credentials.

Install the Dify Console command with Python 3.10 or later. Set `DIFY_BASE_URL`, `ADMIN_API_KEY` and `WORKSPACE_ID` in the environment before use.

```text
python -m pip install ./skills/ai-application-delivery/dify-console-admin-api
dify-console export APP_ID --output app.yml
dify-console import --file app.yml
dify-console confirm IMPORT_ID
```

See [Dify Console Admin API](../skills/ai-application-delivery/dify-console-admin-api/SKILL.md) for creation, overwrite, and pending-import behavior.

## Repository Validation

Install the standalone linter with Python 3.10 or later and run it from the repository root:

```text
python -m pip install ./skills/skill-governance/skill-linter
skill-lint check . --repo-root . --strict --json
```

The command exits with 0 on success, 1 on lint failures, and 2 on invalid usage or an empty scan. In strict mode, warnings count as failures.

Lint every skill and the compatibility entrypoints:

```powershell
.\scripts\run-python.ps1 .\skills\skill-governance\skill-linter\scripts\lint_skill.py . --repo-root .
```

Run the skill-linter unit tests:

```powershell
.\scripts\run-python.ps1 -m unittest discover -s .\skills\skill-governance\skill-linter\tests -v
```

Run the dependency-free Dify structure checks:

```powershell
.\scripts\run-python.ps1 .\skills\ai-application-delivery\quick_validate.py
```

For a generated app, the builder includes [a standalone validator](../skills/ai-application-delivery/dify-dsl-app-builder/scripts/validate_dsl.py). Pass `--input app.json` or `--input app.yml` from the business project. YAML input requires PyYAML. The repository's `quick_validate.py --input` uses the same validator.

## Outputs

- Treat the business project and the skill installation as separate paths. For example, an installed WeChat skill can render into `<business-project>/output/wechat-format/article-workflows/`.
- Agents set the command's working directory to the business project root or pass absolute output arguments. A standalone CLI with a default uses the caller's working directory. Ask for the project root if it is unclear.
- Use the producing skill's frontmatter `name` for its output directory. In a handoff, pass input paths explicitly and keep each stage's output in the same business project. A composite workflow keeps its own intermediates and manifest together.
- Keep configuration and runtime state used for authentication or deduplication in their documented storage. Use the requested destinations for explicit deployments and in-place edits.

## Security

- Never commit real API keys, tokens, passwords, cookies, private endpoints, or account credentials.
- Use `config.example.json` for documentation and ignored `config.json` files for local values.
- Database operations are read-only by default; writes and DDL require explicit authorization.
- Export Dify DSL with `include_secret=false` unless the user explicitly requires otherwise.
- Request approval before installing packages, downloading models, or using browser session state.

## Maintenance Checklist

When adding or moving a skill:

1. Keep the folder name equal to the `SKILL.md` frontmatter `name`.
2. Update `docs/skill-index.md` and affected documentation.
3. Check repository-relative commands and hard-coded parent-directory depth.
4. Run the repository linter and relevant smoke tests.
5. Confirm generated or local files remain ignored.
