---
name: technical-article-polisher
description: Use when polishing or reviewing Chinese technical articles, translated drafts, or technical notes for terminology, professional expression, and logical clarity. Preserves author meaning and returns Markdown, terminology changes, and unresolved terms.
---

# Technical Article Polisher

## Overview

Use this skill to improve technical Chinese articles when terminology accuracy matters. Treat the article as technical content first and prose second: preserve the author's claims, check terms against local context, and make changes traceable.

## Workflow

1. Read the full article before editing.
2. Decide whether the article is technical enough to require terminology review. Trigger the terminology pass for AI, software engineering, databases, infrastructure, system architecture, programming, developer tools, product engineering, or similar domains.
3. Identify the article's domain, intended audience, and likely source style:
   - original Chinese technical writing
   - machine-translated draft
   - rough notes or transcript
   - publication-ready article needing professional polish
4. Extract candidate terms and technical expressions from headings, repeated phrases, key claims, diagrams, code-adjacent text, and definitions.
5. Check each important term in context instead of replacing words mechanically.
6. Edit the article for terminology, consistency, and logical clarity.
7. Return the polished article plus a terminology change log.

## Terminology Review Rules

When the article may be machine translated, pay special attention to:

- mistranslated English technical terms
- literal translations that are unnatural in Chinese technical writing
- terms that are correct in isolation but wrong in the surrounding context
- inconsistent translations for the same concept
- ambiguous words such as agent, memory, retrieval, embedding, index, runtime, context, pipeline, orchestration, grounding, alignment, and benchmark
- generic product language replacing precise technical meaning

Prefer established Chinese technical usage when it is clear. If a Chinese term may be ambiguous, use `Chinese term (English original)` on first mention. Preserve English names for APIs, product names, model names, protocols, package names, commands, code identifiers, and terms that are normally used in English by the target audience.

Do not change the author's technical position, add unsupported claims, or simplify a specialized concept into vague marketing language.

## Editing Rules

- Preserve the article's structure unless the structure blocks comprehension.
- Improve sentence flow, transitions, and paragraph logic where needed.
- Keep technical assertions cautious when the source wording is uncertain.
- Use consistent translations for the same concept throughout the article.
- Do not over-polish into promotional copy.
- If a term is uncertain, leave it unchanged or mark it in the notes instead of guessing.

## Output Format

Return results in this order:

1. **Polished Article**
   - Provide the revised article in Markdown.
   - Keep headings, lists, code blocks, links, and quoted material usable.

2. **Terminology Changes**
   - Include every meaningful terminology change.
   - Use this table:

```markdown
| Original term/expression | Revised term/expression | Reason |
|---|---|---|
| ... | ... | ... |
```

3. **Uncertain Terms**
   - List terms that need user confirmation or source checking.
   - Omit this section only when there are no uncertain terms.

## Example User Requests

- "帮我润色这篇技术文章，重点检查术语是否准确，最后列出术语修改。"
- "这篇可能是机器翻译稿，结合上下文检查专业术语。"
- "把这篇 AI 工程文章改得更专业，但不要改原意。"
- "先用技术文章润色 skill 处理，再交给 wechat-format 排版。"
