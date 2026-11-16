import json
import os
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path


FFMPEG = os.environ.get("SKILLS_MANAGER_TEST_FFMPEG") or shutil.which("ffmpeg")


class MediaCommandTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("media-subtitle-to-md"), "Install the media commands")
    def test_subtitle_conversion(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "captions.srt"
            output = Path(temp) / "transcript.md"
            source.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello world!\n", encoding="utf-8")
            subprocess.run(
                ["media-subtitle-to-md", str(source), "--output", str(output)],
                check=True, capture_output=True, timeout=30,
            )
            markdown = output.read_text(encoding="utf-8")
            self.assertIn("00:00:01", markdown)
            self.assertIn("Hello world!", markdown)

    @unittest.skipUnless(FFMPEG and shutil.which("media-extract-audio"), "Install the media commands and FFmpeg")
    def test_extracts_mono_16_khz_audio_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "stereo.wav"
            with wave.open(str(source), "wb") as stream:
                stream.setparams((2, 2, 8000, 0, "NONE", "not compressed"))
                stream.writeframes(b"\x00" * 3200)

            subprocess.run(
                ["media-extract-audio", str(source), "--ffmpeg", FFMPEG, "--output-dir", temp],
                check=True, capture_output=True, timeout=30,
            )
            manifest = json.loads((Path(temp) / "stereo" / "media-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(manifest["source_media"]), source.resolve())
            with wave.open(manifest["audio"], "rb") as stream:
                self.assertEqual((stream.getnchannels(), stream.getframerate()), (1, 16000))
                self.assertGreater(stream.getnframes(), 0)
