---
name: technical-article-polisher
description: Use when polishing or reviewing Chinese technical articles, translated drafts, or technical notes for terminology, professional expression, and logical clarity. Preserves author meaning and returns Markdown, terminology changes, and unresolved terms.
---

# Technical Article Polisher

## Overview

Use this skill to improve technical Chinese articles when terminology accuracy matters. Treat the article as technical content first and prose second: preserve the author's claims, check terms against local context, and make changes traceable.

## Workflow

1. Read the complete article; identify domain, audience and whether it is translated or rough material. Preserve the author's claims and structure unless structure blocks comprehension.
2. Check important terms in context, especially literal translations, inconsistent names and ambiguous concepts such as agent, memory, embedding, runtime and grounding. Prefer established Chinese usage; explain ambiguity with the English original on first use. Preserve APIs, product names, protocols, commands and identifiers.
3. Improve clarity, transitions and consistency without adding claims, promotional language or stronger certainty. Leave unresolved terms unchanged and record questions rather than guessing.
4. Return usable Markdown and every meaningful terminology change in the contract below. Reuse existing source notes; do not reconstruct a source article or generate visuals during a polishing-only request.

For requested WeChat rendering, hand the final Markdown to `wechat-format` with `--preserve-content`, so its AI polishing does not run again. For rewriting raw sources into a new argument use `technical-source-to-public-article` instead.

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
