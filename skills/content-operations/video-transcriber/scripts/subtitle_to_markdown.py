#!/usr/bin/env python3
"""Convert subtitle files into a readable Markdown transcript."""

from __future__ import annotations

import argparse
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


TIMESTAMP_LINE = re.compile(
    r"(?P<start>(?:\d{1,2}:)?\d{2}:\d{2}[,.]\d{2,3})\s+-->\s+"
    r"(?P<end>(?:\d{1,2}:)?\d{2}:\d{2}[,.]\d{2,3})"
)
INLINE_TIMESTAMP = re.compile(r"<(?:\d{1,2}:)?\d{2}:\d{2}[.]\d{2,3}>")
HTML_TAG = re.compile(r"<[^>]+>")
SRT_INDEX = re.compile(r"^\d+$")
ASS_OVERRIDE_TAG = re.compile(r"\{[^}]*\}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert SRT, VTT, ASS/SSA, TTML, Bilibili JSON, or YouTube json3 subtitles to Markdown.")
    parser.add_argument("input", help="Input subtitle file (.srt/.vtt/.ass/.ssa/.ttml/.json/.json3).")
    parser.add_argument("--output", help="Output Markdown file. Defaults under output/video-transcriber in the calling project.")
    parser.add_argument(
        "--merge-window",
        type=int,
        default=20,
        help="Seconds per paragraph bucket for timestamped transcript output.",
    )
    parser.add_argument(
        "--title",
        default="Transcript",
        help="Markdown title.",
    )
    return parser.parse_args()


def timestamp_to_seconds(value: str) -> int:
    parts = value.replace(",", ".").split(":")
    if len(parts) == 2:
        hours, minutes, seconds = "0", *parts
    elif len(parts) == 3:
        hours, minutes, seconds = parts
    else:
        raise ValueError(f"Unsupported subtitle timestamp: {value}")
    return int(hours) * 3600 + int(minutes) * 60 + int(float(seconds))


def seconds_to_timestamp(value: int) -> str:
    hours = value // 3600
    minutes = (value % 3600) // 60
    seconds = value % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def clean_text(line: str) -> str:
    line = INLINE_TIMESTAMP.sub("", line)
    line = HTML_TAG.sub("", line)
    line = html.unescape(line)
    return " ".join(line.split())


def read_text_cues(path: Path) -> list[tuple[int, str]]:
    cues: list[tuple[int, str]] = []
    current_start: int | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_start, current_lines
        if current_start is None:
            current_lines = []
            return
        text = clean_text(" ".join(current_lines))
        if text:
            cues.append((current_start, text))
        current_start = None
        current_lines = []

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        if line == "WEBVTT" or line.startswith(("Kind:", "Language:", "NOTE")):
            continue
        match = TIMESTAMP_LINE.search(line)
        if match:
            flush()
            current_start = timestamp_to_seconds(match.group("start"))
            continue
        if SRT_INDEX.match(line):
            continue
        current_lines.append(line)

    flush()
    return cues


def read_bilibili_json_cues(path: Path) -> list[tuple[int, str]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    body = data.get("body")
    if not isinstance(body, list):
        raise SystemExit(f"Unsupported JSON subtitle shape: {path}")

    cues: list[tuple[int, str]] = []
    for item in body:
        if not isinstance(item, dict):
            continue
        text = clean_text(str(item.get("content", "")))
        if not text:
            continue
        try:
            timestamp = int(float(item.get("from", 0)))
        except (TypeError, ValueError):
            timestamp = 0
        cues.append((timestamp, text))
    return cues


def read_youtube_json3_cues(path: Path) -> list[tuple[int, str]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    events = data.get("events")
    if not isinstance(events, list):
        raise SystemExit(f"Unsupported YouTube json3 subtitle shape: {path}")
    cues: list[tuple[int, str]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        segments = event.get("segs")
        if not isinstance(segments, list):
            continue
        text = clean_text("".join(str(segment.get("utf8", "")) for segment in segments if isinstance(segment, dict)))
        if text:
            cues.append((int(event.get("tStartMs", 0)) // 1000, text))
    return cues


def read_ass_cues(path: Path) -> list[tuple[int, str]]:
    cues: list[tuple[int, str]] = []
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        if not raw_line.lstrip().lower().startswith("dialogue:"):
            continue
        fields = raw_line.split(":", 1)[1].split(",", 9)
        if len(fields) < 10:
            continue
        try:
            start = timestamp_to_seconds(fields[1].strip())
        except ValueError:
            continue
        text = ASS_OVERRIDE_TAG.sub("", fields[9]).replace("\\N", " ").replace("\\n", " ")
        text = clean_text(text)
        if text:
            cues.append((start, text))
    return cues


def ttml_time_to_seconds(value: str) -> int:
    value = value.strip()
    if value.endswith("s") and ":" not in value:
        return int(float(value[:-1]))
    return timestamp_to_seconds(value)


def read_ttml_cues(path: Path) -> list[tuple[int, str]]:
    root = ET.fromstring(path.read_text(encoding="utf-8-sig"))
    cues: list[tuple[int, str]] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "p":
            continue
        begin = element.attrib.get("begin")
        if not begin:
            continue
        try:
            start = ttml_time_to_seconds(begin)
        except ValueError:
            continue
        text = clean_text(" ".join(element.itertext()))
        if text:
            cues.append((start, text))
    return cues


def read_cues(path: Path) -> list[tuple[int, str]]:
    suffix = path.suffix.lower()
    if suffix in {".srt", ".vtt"}:
        return read_text_cues(path)
    if suffix in {".ass", ".ssa"}:
        return read_ass_cues(path)
    if suffix in {".ttml", ".xml"}:
        return read_ttml_cues(path)
    if suffix in {".json", ".json3"}:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data.get("body"), list):
            return read_bilibili_json_cues(path)
        if isinstance(data.get("events"), list):
            return read_youtube_json3_cues(path)
        raise SystemExit(f"Unsupported JSON subtitle shape: {path}. Expected Bilibili body[] or YouTube json3 events[].")
    raise SystemExit(f"Unsupported subtitle format: {path.suffix}. Supported: .srt, .vtt, .ass, .ssa, .ttml, .json, .json3")


def dedupe_cues(cues: list[tuple[int, str]]) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    last_text = ""
    for timestamp, text in cues:
        if not text:
            continue
        if text == last_text:
            continue
        if last_text and text.startswith(last_text + " "):
            if result:
                result[-1] = (timestamp, text)
            last_text = text
            continue
        result.append((timestamp, text))
        last_text = text
    return result


def render_markdown(title: str, cues: list[tuple[int, str]], merge_window: int) -> str:
    lines = [f"# {title}", ""]
    if not cues:
        lines.append("_No subtitle text found._")
        return "\n".join(lines) + "\n"

    bucket_start: int | None = None
    bucket_text: list[str] = []

    def flush_bucket() -> None:
        nonlocal bucket_start, bucket_text
        if bucket_start is None or not bucket_text:
            return
        paragraph = " ".join(bucket_text)
        lines.append(f"[{seconds_to_timestamp(bucket_start)}] {paragraph}")
        lines.append("")
        bucket_start = None
        bucket_text = []

    for timestamp, text in cues:
        if bucket_start is None:
            bucket_start = timestamp
        if timestamp - bucket_start >= merge_window:
            flush_bucket()
            bucket_start = timestamp
        bucket_text.append(text)

    flush_bucket()
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input subtitle does not exist: {input_path}")
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else Path.cwd() / "output" / "video-transcriber" / input_path.stem / input_path.with_suffix(".md").name
    )
    cues = dedupe_cues(read_cues(input_path))
    if not cues:
        raise SystemExit(f"No usable subtitle cues found: {input_path}. Check the selected subtitle track or use ASR.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_markdown(args.title, cues, args.merge_window),
        encoding="utf-8",
    )
    print(f"Wrote: {output_path}")
    print(f"Cues: {len(cues)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
