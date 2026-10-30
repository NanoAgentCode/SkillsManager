---
name: video-transcriber
description: Use when converting local audio/video, subtitles, authorized online video, or 视频号 material into transcripts, SRT/VTT, summaries, meeting notes, or article-ready notes. Prefer usable captions; use authorized ASR when captions are unavailable.
---

# Video Transcriber

## Overview

Use this skill to turn subtitles, local media, or user-authorized online media into usable text artifacts. Always prefer existing subtitles/captions over ASR because they are cheaper, faster, and often cleaner. Use audio extraction and speech recognition only when no usable subtitle source exists or when the user explicitly asks to re-transcribe the audio.

## Workflow

1. Confirm the input source and desired output shape:
   - existing `.srt`, `.vtt`, `.ass`, `.ssa`, `.ttml`, `.json3`, or Bilibili AI subtitle `.json` file
   - local media path
   - direct online media URL
   - platform page URL supported by a local downloader
   - WeChat Channels/视频号 material supplied as a saved file, public share link, direct media URL, or user-authorized browser/session export
   - plain transcript
   - timestamped Markdown
   - SRT or VTT subtitles
   - meeting notes, summary, article draft, or terminology-polished text
2. If the source is online, confirm the user is authorized to download or process it. Do not bypass paywalls, private access controls, login restrictions, DRM, or platform anti-abuse controls.
3. Look for usable subtitles first:
   - if the user provided a subtitle file, parse it directly
   - if a local media file has sidecar subtitles with the same stem, use them first
   - if the online platform exposes captions, download captions before downloading media
   - if multiple caption tracks exist, prefer human/original-language captions, then translated captions, then auto-generated captions
   - treat a subtitle as usable only when conversion produces one or more text cues; an empty track is a failed subtitle route, not a transcript
4. When subtitle extraction fails or subtitles are absent, incomplete, wrong-language, or explicitly rejected, explain the concrete failure and ask whether to try local ASR. If the user already requested or approved ASR, continue without asking again. Follow the fallback below; subtitle failure alone does not authorize a model download or cloud transcription.
5. For local files, check whether the input file exists and identify its extension. Common media inputs include `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`, `.mp3`, `.m4a`, `.wav`, `.aac`, and `.flac`.
6. Check local tools before asking the user to install anything:
   - `ffmpeg -version`
   - `ffprobe -version`
   - URL downloaders such as `yt-dlp` only when an online source must be fetched
   - available ASR tools such as `whisper`, `faster-whisper`, `insanely-fast-whisper`, local model wrappers, or approved API/CLI tools
7. Use `scripts/subtitle_to_markdown.py` for subtitle-first transcript drafts, or `scripts/extract_audio.py` for media acquisition/audio extraction when ASR is needed.
8. Transcribe extracted audio with the best available ASR tool only after the subtitle path is exhausted.
9. Normalize the transcript:
   - preserve timestamps when available
   - split long paragraphs by topic or speaker changes
   - mark uncertain words with `[unclear]` instead of inventing content
   - do not fabricate missing speech when audio is inaudible
10. Save final artifacts under `output/video-transcriber/<media-stem>/` by default and report the paths.

## Acquisition routes

Before acquiring captions or media, read the matching section of [acquisition-and-asr.md](references/acquisition-and-asr.md):

- **Subtitle-First Path**: supported formats, conversion, and caption discovery.
- **Online Video Sources / WeChat Channels**: authorized downloads, credentials, and platform limits.
- **Audio Extraction And ASR Fallback / Transcription Tool Selection**: required before ASR, including cached-model checks, download approval, raw-output preservation, timestamp coverage, and command templates.

Do not download a model or upload media merely because subtitle extraction failed.

## Technical Terminology Proofreading

For technical recordings, review model/product names, acronyms, code identifiers, and recurring homophone errors after transcription. Preserve the raw ASR files and write corrections to separate deliverables.

- Verify proposed corrections against the audio and visible video context; use official documentation when spelling remains uncertain. A plausible technical term alone is not evidence that it was spoken.
- Correct only supported terms, preserving meaning and timestamps. Do not silently rewrite the speaker's factual claims. Mark unresolved words with `[unclear]` and their timestamps rather than guessing.
- Save `terminology-changes.md` with timestamp, original text, corrected term, and evidence or uncertainty. Apply confirmed corrections consistently to the corrected text and subtitles; avoid global replacement of ambiguous ordinary words.
- If full publication-level polishing is requested and `technical-article-polisher` is available, use it after preserving the transcript. Term correction alone does not require restructuring the content into an article.

Review these acceptance cases when updating this workflow: usable captions stop the ASR route; failed caption capture prompts for local ASR; prior ASR approval plus a cached compatible model proceeds without another download prompt; a missing model requires size/install disclosure and approval; inaccessible audio remains a blocker; uncertain terminology stays marked and raw recognition remains intact.

## Output Rules

- Keep subtitle files, raw extracted audio, ASR output, cleaned transcript, and summaries in the same media-specific output folder.
- For online sources, keep the downloaded `source.<ext>` file with the extracted audio unless the user asks to delete intermediates.
- Use UTF-8 for transcript files.
- In `media-manifest.json` or final notes, record whether the transcript came from `subtitles`, `auto-captions`, or `asr`.
- For Chinese speech, output polished Chinese only after preserving an original transcript or timestamped draft.
- For multilingual speech, preserve language switches unless the user asks for translation.
- If speaker labels are not available, infer them conservatively as `Speaker 1`, `Speaker 2`, etc. only when turns are clear.
- If the user wants publication-ready Chinese technical text, run the transcript through `skills/content-operations/technical-article-polisher` after transcription.
- If the user wants a WeChat article, use `skills/content-operations/wechat-format` only after the transcript has been cleaned and structured.

## Common Deliverables

Plain transcript:

```text
transcript.md
```

Timestamped transcript:

```text
[00:00:03] Opening remarks...
[00:00:18] Main topic...
```

Subtitle files:

```text
subtitles.srt
subtitles.vtt
```

Meeting notes:

```markdown
# Meeting Notes

## Summary

## Decisions

## Action Items
```

## Safety And Privacy

- Treat user-provided media as private local content.
- Download or process online videos only when the user is authorized to do so.
- Do not upload media, audio, URLs, cookies, browser state, or transcripts to external services unless the user explicitly approves that route.
- Do not expose API keys or local ASR configuration from ignored config files.
- Do not commit downloaded media, cookies, tokens, or transcripts unless the user explicitly asks and the repository policy allows it.
- When credentials are needed, request the least-privileged usable credential route and keep credentials out of repository artifacts.
- If a video appears copyrighted or third-party, provide transcripts only for user-authorized use and avoid redistributing long copyrighted content beyond the user's requested private processing.
