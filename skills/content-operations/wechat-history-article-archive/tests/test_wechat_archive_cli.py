import json
import shutil
import subprocess
import tempfile
import threading
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


@unittest.skipUnless(shutil.which("wechat-archive"), "Install wechat-archive")
class WechatArchiveCommandTests(unittest.TestCase):
    def test_extract_fetch_and_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.txt"
            urls = root / "urls.txt"
            url = "https://mp.weixin.qq.com/s?__biz=demo&mid=123&idx=1&sn=demo"
            source.write_text(f"{url}\n{url}\n", encoding="utf-8")
            self.run_command("extract", "--input", str(source), "--output", str(urls))
            self.assertEqual(urls.read_text(encoding="utf-8").splitlines(), [url])

            (root / "page.html").write_text(
                '<meta property="og:title" content="Sample"><div id="js_content"><p>Archive body</p></div>',
                encoding="utf-8",
            )
            handler = partial(SimpleHTTPRequestHandler, directory=str(root))
            archive = root / "archive"
            with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
                worker = threading.Thread(target=server.serve_forever)
                worker.start()
                try:
                    urls.write_text(f"http://127.0.0.1:{server.server_port}/page.html\n", encoding="utf-8")
                    self.run_command("fetch", "--input", str(urls), "--output-dir", str(archive), "--keep-html")
                finally:
                    server.shutdown()
                    worker.join()

            [record] = json.loads((archive / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "ok")
            article = Path(record["article_dir"])
            self.assertTrue((article / "meta.json").is_file())
            markdown = article / "article.md"
            self.assertIn("Archive body", markdown.read_text(encoding="utf-8"))
            markdown.unlink()
            self.run_command("export", "--archive-dir", str(archive))
            self.assertIn("Archive body", markdown.read_text(encoding="utf-8"))
            self.assertTrue((article / "article.html").is_file())

    def run_command(self, *args):
        result = subprocess.run(["wechat-archive", *args], capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
