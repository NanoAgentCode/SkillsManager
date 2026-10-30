> Read only for the mode linked from SKILL.md. Unless stated otherwise, command and resource paths are relative to the skill directory, not this references directory.

## Long Document Mode

Use this mode for books, long reports, papers, manuals, transcripts, research packs, or any input too large or too detailed for one readable map.

Default mode selection:

- If the user explicitly asks for overview-first, chapter/section expansion, conversational expansion, or on-demand expansion, use Long Document Mode regardless of page count.
- For papers up to 25 pages, default to a single paper overview mindmap unless the user asks for interactive expansion.
- For English text up to roughly 20,000 words, default to a single overview mindmap unless the user asks for interactive expansion.
- For Chinese text up to roughly 30,000 characters, default to a single overview mindmap unless the user asks for interactive expansion.
- For papers over 25 pages, default to Long Document Mode.
- For English text over roughly 20,000 words or Chinese text over roughly 30,000 characters, default to Long Document Mode when the content has document-like structure.
- For books, manuals, long reports, research packs, or documents over roughly 25 pages, default to Long Document Mode.
- If a document is 25 pages or fewer but has unusually dense structure, many appendices, many experiments, or many nested sections, prefer a compact overview and mention that sections can be expanded on request.
- If a long document user explicitly asks for one complete map, generate a compressed single overview and note that fine detail will be omitted.

Enter this mode when the user explicitly asks for any of these patterns:

- "overview first, then expand selected sections"
- "default overview only"
- "interactive chapter expansion"
- "conversational expansion"
- "section-by-section mindmap"
- "总览图"
- "默认只展示总览"
- "用户可选章节"
- "章节展开"
- "对话式展开"
- "按需展开"

Default behavior:

1. Build a compact overview map first.
   - Show the document title, purpose, major parts/chapters/sections, key themes, and important conclusions.
   - Do not include paragraph-level detail in the overview.
   - Keep each top-level branch selectable by name in the conversation, for example `Chapter 3`, `Methods`, or `Risk Analysis`.
   - Use the same section labels in the overview, section index, and detail maps.
   - If the overview is thematic, put original chapter/section labels under each theme so follow-up expansion has a clear target.
2. Preserve an internal section index in the conversation or a sibling Markdown file when useful.
   - Include stable section labels, source page/heading hints when available, and a one-line summary.
   - Use this index to answer follow-up requests such as "expand chapter 2" or "show the methods section".
3. On user selection, generate a separate detail mindmap for that chapter or section.
   - The detail map should use the selected section as the root.
   - Include local structure, key claims, evidence, examples, formulas, figures, risks, or terms as appropriate to the source type.
   - Keep it separate from the overview instead of appending everything into one giant map.
   - Make the detail root exactly match the selected overview/index label unless the user asks for a renamed concept map.
4. For nested follow-ups, repeat the pattern.
   - Section detail map -> subsection detail map -> concept map when needed.
   - Stop expanding when the requested level is readable and useful.

Recommended output structure:

```text
output/mindmap-builder/
  overview.md
  overview.html
  sections/
    chapter-01.md
    chapter-01.html
    methods.md
    methods.html
```

Name files with short stable slugs. If generating only one selected section, it is fine to create just the overview plus that section map.

Interaction pattern:

```text
source document
  -> section index
  -> overview mindmap using the same labels
  -> user selects an overview/index label in chat
  -> selected-section mindmap with the same root label
```

For papers:

- Overview branches usually include `Question`, `Method`, `Data`, `Findings`, `Limitations`, and `Implications`.
- Detail branches should preserve technical terms, definitions, datasets, metrics, equations, and experiment names when they matter.

For reports:

- Overview branches usually include `Background`, `Current State`, `Findings`, `Risks`, `Recommendations`, and `Next Steps`.
- Detail branches should preserve decision points, owners, numbers, timelines, and dependencies when present.

For books:

- Overview branches usually include `Part/Chapter Structure`, `Core Argument`, `Key Concepts`, `Characters/Actors` when relevant, and `Takeaways`.
- Detail branches should summarize chapter arcs, important scenes/examples, concepts, and cross-chapter links.
