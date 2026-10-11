# Skill Index

This is the canonical repository skill catalog. It summarizes the reusable skills in this repository; treat each `SKILL.md` as the source of truth for execution details.

## Content Operations

Use this group when the request is about turning media, notes, drafts, or archived material into publishable content.

- `skills/content-operations/video-transcriber/SKILL.md`: transcript, subtitle, summary, meeting-note, and article-draft workflows from local media, approved online videos, existing captions, YouTube captions, Bilibili subtitle JSON, or user-authorized WeChat Channels material.
- `skills/content-operations/technical-article-polisher/SKILL.md`: Chinese technical article polishing, machine-translation cleanup, terminology checks, and publication-ready Markdown.
- `skills/content-operations/technical-source-to-public-article/SKILL.md`: evidence-grounded transformation of papers, documentation, reports, transcripts, repositories, web pages, or mixed technical sources into readable publication-ready Simplified Chinese public articles with traceable claims.
- `skills/content-operations/technical-article-visual-director/SKILL.md`: coherent visual direction, production routing, asset generation when supported, inspection, captions, accessibility, and Markdown placement for technical articles.
- `skills/content-operations/wechat-format/SKILL.md`: WeChat official-account packaging through `scripts/article_workflow.py`, including upstream source-note and visual-plan handoff, local asset staging, terminology/structure processing, a 26-theme gallery, themed outputs, optional covers, and draft publishing.
- `skills/content-operations/wechat-history-article-archive/SKILL.md`: authorized historical WeChat article backup from lawful `mp.weixin.qq.com/s?...` URL sources, with Markdown, metadata, indexes, and local images by default.
- `skills/content-operations/wechat-cover/SKILL.md`: cover-image generation for WeChat articles; installed alongside `wechat-format` and reuses its image-generation script.
- `skills/content-operations/office-cli-skill/SKILL.md`: structured DOCX, XLSX, and PPTX creation, inspection, validation, proofreading, and editing with an installed `officecli` executable, including template-based PowerPoint reconstruction guidance.
- `skills/content-operations/official-format-pro/SKILL.md`: Markdown, TXT, or DOCX conversion into Chinese party-and-government official-document Word layouts based on the bundled GB/T 9704-2012 formatting summary.

## Knowledge Structuring And Visualization

Use this group when the request is about systematic technical understanding, knowledge frameworks, diagrams, mindmaps, visual explanation, or offline knowledge views.

- `skills/knowledge-visualization/obsidian-memory/SKILL.md`: local Obsidian Vault workflow with ranked single- or multi-keyword retrieval, All/Any matching, reviewable candidate memories, stale or superseded record handling, and a visual bidirectional-link index.
- `skills/knowledge-visualization/obsidian-memory-cleanup/SKILL.md`: full or scoped semantic cleanup for Obsidian long-term memory vaults, including deduplication, fragment consolidation, current-source fact verification, reclassification, lifecycle conflict handling, and deterministic structural audits.
- `skills/knowledge-visualization/technical-cognition-framework/SKILL.md`: evidence-based frameworks for systematically understanding a technology through its definition, concept relationships, motivation, construction methods, scenarios, boundaries, common confusions, and relationship with LLMs and agents; includes Ontology as a worked reference.
- `skills/knowledge-visualization/drawio-skill/SKILL.md`: code dependency analysis and editable `.drawio` import/module/package dependency graphs for Python, JavaScript/TypeScript, Go, and Rust codebases, with local draw.io CLI export when available; do not select it for general visualization requests.
- `skills/knowledge-visualization/excalidraw/SKILL.md`: clean `.excalidraw` flowcharts, architecture sketches, process diagrams, relationship maps, and whiteboard-style visual explanations with Kroki SVG or local PNG/SVG export.
- `skills/knowledge-visualization/mindmap-builder/SKILL.md`: single-file offline markmap HTML generation from PDFs, notes, outlines, reports, papers, books, or other documents; supports overview-first long document mode.
- `skills/knowledge-visualization/mindmap-publisher/SKILL.md`: static publishing for already generated offline mindmap HTML folders when the user explicitly asks to publish or host.

## AI Application Delivery

Use this group when the request is about Dify apps, DSL import/export, platform configuration, or delivery verification.

- `skills/ai-application-delivery/dify-console-admin-api/SKILL.md`: Dify Console Admin API automation for app creation, DSL export/import, overwrite import, and pending import confirmation.
- `skills/ai-application-delivery/dify-dsl-app-builder/SKILL.md`: Dify workflow or advanced-chat DSL design, generation, update, import, and verification.

## Engineering Operations

Use this group when the request is about evidence-driven website reconstruction, dependency packaging, database-backed lookup, or diagnosing backend code and contract paths.

- `skills/engineering-operations/website-rebuild/SKILL.md`: authorized public-website reconstruction through scope classification, immutable offline mirroring, client-bundle forensics, source-traceable porting, WebGL or scroll-animation recovery, quantitative parity gates, and optional readable-source delivery; excludes access-control bypass and ordinary greenfield frontend design.
- `skills/engineering-operations/python-offline-dependency-packager/SKILL.md`: interactive dependency-name collection and configured-index version discovery without package downloads when the exact version or target Python is missing; complete requests produce an exact-version bundle with the full transitive dependency closure, target interpreter/platform selectors, file hashes, and one-click offline installers for PowerShell and POSIX shells.
- `skills/engineering-operations/python-db-query/SKILL.md`: safe Python database querying plus Windows/Linux MinIO `mc` integration for bucket/object inspection and guarded downloads, with ignored local configs, read-only defaults, structured output, and explicit authorization boundaries.
- `skills/engineering-operations/backend-log-contract-trace/SKILL.md`: backend log-to-contract tracing across routes/controllers, DTO/VOs, services, mapper XML, SQL columns, cross-service parameters, and database constraints.

## Market Intelligence

Use this group when the request is about market research, public-market impact analysis, or investment-bank style output.

- `skills/market-intelligence/stock-analysis-system/SKILL.md`: local Python FastAPI stock-analysis service for A-share, Hong Kong, U.S. stock, ETF, and LOF technical analysis, including AKShare data retrieval, technical indicators, scoring, and API smoke tests.
- `skills/market-intelligence/us-sector-index-impact-report/SKILL.md`: most recent completed U.S. trading session analysis, Nasdaq/Nasdaq 100 and sector moves, core drivers, U.S. AI capex fundamentals, and Hong Kong/A-share sector implications rendered as standalone HTML. Includes a stable checked-in renderer fixture at `fixtures/sample-report.json`.

## Skill Governance

Use this group when the request is about validating, reviewing, or preparing skills for release.

- `skills/skill-governance/skill-linter/SKILL.md`: skill structure, trigger metadata, resource links, UI metadata, repository catalog sync, platform compatibility entrypoints, and secret hygiene checks.

Primary command:

```powershell
.\scripts\run-python.ps1 .\skills\market-intelligence\us-sector-index-impact-report\scripts\render_investment_bank_html.py `
  --input .\output\us-sector-index-impact-report\report-data.json `
  --output .\output\us-sector-index-impact-report\us-sector-impact-report.html
```

On Windows, use the repository launcher for Python-based skills so commands do not depend on `python` or `py` being on `PATH`. If Python is unavailable, the launcher reports the missing interpreter prerequisite and the locations it checked.

Preview the stable fixture:

```powershell
.\skills\market-intelligence\us-sector-index-impact-report\scripts\preview_sample_report.ps1
```

## Directory Layout

All skills use the `skills/<business-scenario>/<skill-name>/` layout. See [Directory Structure](directory-structure.md) for the complete tree, migration map, and maintenance rules.
