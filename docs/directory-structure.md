# Business Scenario Directory Structure

The repository groups reusable skills by the business outcome they support, rather than by an implementation technology or model provider.

## Layout

```text
skills/
  content-operations/
    article-infographic/
    technical-article-visual-director/
    technical-article-polisher/
    technical-source-to-public-article/
    video-transcriber/
    office-cli-skill/
    official-format-pro/
    wechat-cover/
    wechat-format/
    wechat-history-article-archive/
  knowledge-visualization/
    drawio-skill/
    excalidraw/
    mindmap-builder/
    mindmap-publisher/
    obsidian-memory/
    obsidian-memory-cleanup/
    technical-cognition-framework/
  ai-application-delivery/
    dify-console-admin-api/
    dify-dsl-app-builder/
    context-json-validator-workflow.yml
    quick_validate.py
  engineering-operations/
    docker-app-upgrade/
    backend-log-contract-trace/
    python-offline-dependency-packager/
    python-db-query/
    website-rebuild/
  market-intelligence/
    stock-analysis-system/
    us-sector-index-impact-report/
  skill-governance/
    skill-linter/
```

Generated artifacts do not live under `skills/`. Put them in `output/<skill-name>/` unless the user provides another output path.

## Scenario Boundaries

| Scenario | Responsibility | Typical handoff |
|---|---|---|
| `content-operations` | Turn source media, drafts, and archived material into publication-ready content. | A transcript can flow to technical polishing and then WeChat formatting. |
| `knowledge-visualization` | Turn technical topics, systems, or documents into cognition frameworks, external memory, diagrams, mindmaps, and publishable knowledge artifacts. | Obsidian Memory preserves reviewable long-term context; visual skills turn structures into diagrams or offline views. |
| `ai-application-delivery` | Design, create, import, update, and verify Dify applications and DSL. | DSL App Builder uses Console Admin API for remote delivery work. |
| `engineering-operations` | Reconstruct authorized public websites with evidence and parity gates, package development dependencies, query operational data safely, and trace backend failures through code and data contracts. | A website rebuild progresses from a verified immutable mirror to a traceable port; a Python package bundle can be transferred to an offline host; a log trace may use read-only database evidence when authorized. |
| `market-intelligence` | Run technical market analysis and produce cross-market impact research. | Structured market data is rendered into a standalone research report. |
| `skill-governance` | Validate skill structure, metadata, references, compatibility, and secret hygiene. | Run before committing, installing, or releasing a skill. |

## Migration Map

| Previous category | New business scenario |
|---|---|
| `media/`, `writing/`, `wechat/` | `skills/content-operations/` |
| `diagram/`, `mindmap/` | `skills/knowledge-visualization/` |
| `dify/` | `skills/ai-application-delivery/` |
| `database/`, `debugging/` | `skills/engineering-operations/` |
| `market/` | `skills/market-intelligence/` |
| `quality/` | `skills/skill-governance/` |

## Maintenance Rules

1. Keep the concrete skill folder name equal to the `name` in its `SKILL.md` frontmatter.
2. Add a skill to the scenario that best matches the user's requested outcome. Do not add a new scenario for a single implementation technology.
3. Keep cross-skill references repository-relative when documenting invocation paths. Use relative Markdown links only when the linked file is inside the same scenario and the relationship is stable.
4. Keep generated files, local configs, credentials, and test outputs under ignored paths. Default generated artifacts belong under the repository-level `output/` directory.
5. When moving or adding a skill, update `docs/skill-index.md` and any affected operational documentation. Keep `README.md` and `AGENTS.md` as concise entrypoints, then check scripts for hard-coded parent-directory depth and repository-relative commands.
6. Validate the result from the repository root:

   ```powershell
   .\scripts\run-python.ps1 .\skills\skill-governance\skill-linter\scripts\lint_skill.py . --repo-root .
   & $Python .\skills\ai-application-delivery\quick_validate.py
   ```
