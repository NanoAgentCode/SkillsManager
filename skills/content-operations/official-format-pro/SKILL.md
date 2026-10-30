---
name: official-format-pro
description: Use for 公文排版 or 红头文件 when supplied text, Markdown, or DOCX needs Chinese government-document formatting based on GB/T 9704-2012. Produces DOCX; excludes generic Word documents without this formatting requirement.
---

# 党政机关公文排版

Use the bundled script to turn supplied content into a reviewable Word document. Treat the reference as a formatting summary, not as legal or records-management advice.

## Prerequisite

The script requires Python 3 and `python-docx`. From this repository on Windows, use the repository Python launcher. If `python-docx` is missing, report the prerequisite; installing packages requires the user's approval.

Read [references/gb9704-2012.md](references/gb9704-2012.md) when choosing page, font, header, addressee, signature, attachment, page-number, or colophon options.

## Workflow

1. Confirm the title, source content, requested output format, and any official-document elements the user supplied. Do not invent an issuing body, document number, classification, urgency, signatory, addressee, dates, distribution list, or disclosure note.
2. Save direct chat content as UTF-8 text in a temporary or output workspace. Preserve an uploaded source and write the result to a separate file unless overwrite is explicit.
3. Generate a DOCX with the repository launcher:

   ```powershell
   .\scripts\run-python.ps1 .\skills\content-operations\official-format-pro\scripts\official_format.py `
     --title "公文标题" `
     --input .\output\official-format-pro\content.md `
     --output .\output\official-format-pro\output.docx
   ```

4. Add only user-confirmed optional flags. Run `--help` for the complete parameter list.
5. Open or render the result with an available Word-document workflow and check content completeness, hierarchy, page layout, fonts/fallbacks, page numbers, and requested official elements before delivery.

For DOCX input, paragraphs and tables are preserved in source order. Tables are converted into clearly marked text rows for formal-document review; review the result when a source contains complex merged cells, images, charts, or text boxes.

PDF output additionally requires LibreOffice. If it is unavailable, deliver the DOCX and clearly report that PDF conversion was not completed.

## Important limits

- Automatic formatting does not establish a document's official status, authenticity, secrecy classification, or approval.
- Font fallback can change pagination. Visually verify on the target system, especially when 方正小标宋简体, 仿宋, 楷体, or 黑体 is unavailable.
- Keep generated artifacts under `output/official-format-pro/` unless the user gives another path.
