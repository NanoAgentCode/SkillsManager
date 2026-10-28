---
name: video-transcriber
description: Convert local media files, existing subtitle files, approved online video URLs, or user-authorized WeChat Channels/video-account material into transcripts, subtitles, summaries, meeting notes, or article-ready notes. Use when the user asks to read video content, transcribe recordings, convert video/audio to text, process local SRT/VTT subtitles, process an online video link, handle a WeChat video account/视频号 item, produce SRT/VTT/Markdown transcripts, extract meeting notes from media, or prepare spoken content for downstream writing and formatting.
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

## Subtitle-First Path

Use this path before downloading media or running speech recognition.

Local subtitle file, including Bilibili AI subtitle JSON saved from an authorized browser session:

```powershell
$Python = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $Python .\skills\content-operations\video-transcriber\scripts\subtitle_to_markdown.py `
  .\output\video-transcriber\demo\source.en.vtt `
  --output .\output\video-transcriber\demo\transcript.md
```

Portable shell:

```bash
python3 ./skills/content-operations/video-transcriber/scripts/subtitle_to_markdown.py \
  ./output/video-transcriber/demo/source.en.vtt \
  --output ./output/video-transcriber/demo/transcript.md
```

For online videos, first inspect and fetch subtitles:

```powershell
yt-dlp --skip-download --list-subs "https://example.com/video"
yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs "en.*,zh.*,en,zh" --sub-format vtt `
  -o ".\output\video-transcriber\demo\source.%(ext)s" `
  "https://example.com/video"
```

If this produces a usable `.vtt` or `.srt`, convert it to Markdown and stop before downloading video/audio. Run ASR only if the subtitle track is missing, empty, badly misaligned, or not in a usable language.

### Subtitle format support

`subtitle_to_markdown.py` supports these local caption inputs directly:

| Format | Support | Notes |
|---|---|---|
| `.srt` / `.vtt` | Direct | Supports `HH:MM:SS.mmm` and short `MM:SS.mmm` timestamps. |
| `.ass` / `.ssa` | Direct | Reads dialogue events and removes ASS override tags. |
| `.ttml` | Direct | Reads timed `<p begin="...">` cues. |
| Bilibili subtitle `.json` | Direct | Requires a `body[]` array with `from` and `content`. |
| YouTube `.json3` / `.json` | Direct | Requires `events[]` with `tStartMs` and `segs[].utf8`. |
| Other caption JSON/XML formats | Convert first | Convert to SRT/VTT, or use ASR when no supported caption export exists. |

The converter exits with a clear failure when no usable text cues are found and does not write an empty Markdown transcript. Do not send that failed output to polishing or formatting; select another caption track or continue with the ASR fallback.

## Online Video Sources

For URL inputs, prefer this order:

1. List and download subtitles/captions with a local downloader.
2. Use a direct downloadable subtitle or media URL when the user provides one.
3. Use an existing local downloader only when it supports the platform and the user is authorized to process the video.
4. If the platform requires login, browser state, cookies, account access, or other credentials, pause and ask the user for the least-privileged credential route:
   - a local exported video/audio/subtitle file
   - a direct temporary media or subtitle URL
   - a `cookies.txt` file path the user has intentionally exported
   - approval to use a currently logged-in browser/session if the environment exposes browser automation
   - platform API credentials only when the user owns or administers the content
5. If download is blocked by platform controls or credentials are not provided, stop and explain the limitation instead of attempting circumvention.

Run URL downloads only with an explicit flag:

```powershell
$Python = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $Python .\skills\content-operations\video-transcriber\scripts\extract_audio.py `
  "https://example.com/video-page-or-media-url" `
  --allow-url-download `
  --output-dir .\output\video-transcriber
```

Portable shell:

```bash
python3 ./skills/content-operations/video-transcriber/scripts/extract_audio.py \
  "https://example.com/video-page-or-media-url" \
  --allow-url-download \
  --output-dir ./output/video-transcriber
```

The script uses `yt-dlp` by default for URL input. If the environment has another approved downloader, pass a custom command:

```powershell
& $Python .\skills\content-operations\video-transcriber\scripts\extract_audio.py "https://example.com/video.mp4" `
  --allow-url-download `
  --download-command 'yt-dlp -o "{output_template}" "{url}"'
```

Supported download placeholders are `{url}`, `{output_template}`, `{output_dir}`, and `{stem}`.

When credentials are required, do not ask the user to paste passwords, raw cookies, tokens, or secrets into chat. Prefer a local file path, browser-session approval, or an exported media/subtitle artifact. Do not save credentials in `output/`, `config.json`, transcripts, manifests, or repository files.

### Known Platform Paths

Use these platform-specific paths when they apply:

- YouTube: use `yt-dlp --skip-download --list-subs` first, then `--write-subs --write-auto-subs` to fetch `.vtt` captions. Convert the resulting subtitle file with `scripts/subtitle_to_markdown.py`. Download media only when captions are absent or unusable.
- Bilibili: first try public downloader/API subtitle discovery. If public discovery returns no usable subtitle but the user authorizes a logged-in browser session, open the video page, trigger the subtitle menu, select the desired language, and capture the subtitle response. Bilibili AI subtitle JSON can be saved and converted directly with `scripts/subtitle_to_markdown.py`.
- WeChat Channels / 视频号: treat browser URL support as limited. Public share links may redirect to phone WeChat or require WeChat-only state, so prefer exported video files, screen recordings, direct temporary media URLs, or subtitle files.

## WeChat Channels / 视频号

WeChat video-account sources are often tied to app login state, temporary URLs, or platform restrictions. Use these routes in order:

1. Prefer a user-provided local subtitle file if one exists.
2. Prefer a user-provided local video file exported from WeChat.
3. Use a direct subtitle or media URL only if the user provides it and it is accessible in the current environment.
4. Use a public share URL only if a local downloader can handle it without bypassing access controls.
5. For logged-in or private material, pause and ask the user for credentials or an authorized artifact:
   - exported/saved video file
   - screen recording
   - direct temporary media URL
   - exported cookies file path or browser-session approval
   - owner/admin API credentials if the user operates the account
6. If a share link only opens a QR/login handoff and playback remains inside phone WeChat, report that Chrome/browser subtitle capture is unavailable and ask for a saved video, recording, direct media URL, or subtitle file.
7. Do not store WeChat cookies, tokens, browser profiles, or private session files in the repository.

Keep WeChat artifacts in the normal output folder:

```text
output/video-transcriber/<wechat-video-stem>/
  source.<ext>
  audio.wav
  media-manifest.json
  transcript.md
```

If a WeChat source cannot be downloaded safely, still support the task by guiding the user to provide one of:

- a subtitle file
- the saved `.mp4` / `.mov` file
- a direct temporary media URL they are authorized to use
- a screen recording file
- an already exported audio file

## Audio Extraction And ASR Fallback

Use this path only when no usable subtitle file or platform caption track exists. Prefer the bundled script instead of hand-writing fragile `ffmpeg` commands.

Before starting local ASR:

1. Offer the fallback after a concrete subtitle failure, including browser/tool capture failures: “字幕提取失败，是否尝试本地语音转写？” Distinguish an unavailable subtitle route from unavailable media; ASR still needs accessible audio.
2. Inspect the selected Python environment, installed ASR packages, configured model directories, and relevant model caches (for example Hugging Face, Whisper, or ModelScope). Reuse a complete compatible model already on disk, using its local path or the tool's offline/local-files-only option to prevent an implicit download. Do not treat partial downloads as usable models.
3. If tools or a suitable model are missing, state the proposed model, verified approximate download size, and required installation before requesting approval. Reuse prior approval for that same installation/model; ask again only if the proposed download or processing destination materially changes. Do not fetch a larger replacement model silently.
4. Reuse existing audio for this video when available. Otherwise acquire accessible audio through the authorized downloader/API route. A subtitle login failure does not imply that public audio is inaccessible; try an ordinary supported audio route without bypassing access controls. If audio is also blocked, request a local media file or an authorized session route.
5. Save raw timestamped recognition output before editing. Check nonempty cues, increasing timestamps, and coverage against audio duration; investigate substantial missing sections and report any remaining gap. Label delivery as automatic ASR and state the actual proofreading scope.

Local file:

```powershell
$Python = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $Python .\skills\content-operations\video-transcriber\scripts\extract_audio.py `
  "C:\path\to\video.mp4" `
  --output-dir .\output\video-transcriber
```

Portable shell:

```bash
python3 ./skills/content-operations/video-transcriber/scripts/extract_audio.py ./input/video.mp4 --output-dir ./output/video-transcriber
```

The script creates:

```text
output/video-transcriber/<media-stem>/
  audio.wav
  media-manifest.json
```

Default audio settings are mono 16 kHz WAV, which works well for most speech recognition tools.

## Transcription Tool Selection

Use the most reliable tool already available in the environment. Do not download large models or call paid/cloud APIs without user approval.

Recommended local command patterns:

```powershell
whisper .\output\video-transcriber\demo\audio.wav --language Chinese --task transcribe --output_format srt --output_dir .\output\video-transcriber\demo
```

```powershell
faster-whisper .\output\video-transcriber\demo\audio.wav --language zh --output_dir .\output\video-transcriber\demo
```

If a command-line transcriber is available, `extract_audio.py` can run it after extraction with placeholders:

```powershell
& $Python .\skills\content-operations\video-transcriber\scripts\extract_audio.py .\input\demo.mp4 `
  --output-dir .\output\video-transcriber `
  --transcribe-command 'whisper "{audio}" --language Chinese --task transcribe --output_format srt --output_dir "{output_dir}"'
```

Supported placeholders are `{audio}`, `{output_dir}`, `{stem}`, and `{transcript}`. The script writes `transcript.txt` as the default placeholder target, but the chosen ASR tool may emit other files such as `.srt`, `.vtt`, `.json`, or `.txt`.

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
