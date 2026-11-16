from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "download_package.py"
SPEC = importlib.util.spec_from_file_location("download_package", SCRIPT)
assert SPEC and SPEC.loader
download_package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(download_package)


class DownloadPackageTests(unittest.TestCase):
    def test_installed_versions_lists_without_creating_bundle(self) -> None:
        args = download_package.parse_args(["versions", "--package", "requests"], installed=True)
        output = io.StringIO()
        with (
            mock.patch.object(download_package, "list_available_versions", return_value="2.32.5") as versions,
            mock.patch.object(download_package, "create_bundle") as bundle,
            redirect_stdout(output),
        ):
            self.assertEqual(download_package.run(args), 0)
        versions.assert_called_once_with("requests")
        bundle.assert_not_called()
        self.assertIn("2.32.5", output.getvalue())

    def test_installed_bundle_requires_target_python(self) -> None:
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failure:
            download_package.parse_args(["bundle", "--package", "requests", "--version", "2.32.5"], installed=True)
        self.assertEqual(failure.exception.code, 2)

    def test_creates_bundle_with_transitive_download_command_and_installers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "bundle"
            args = download_package.parse_args(
                [
                    "--package",
                    "requests[socks]",
                    "--version",
                    "2.32.5",
                    "--python-version",
                    "3.11.x",
                    "--output",
                    str(output),
                ]
            )

            def fake_run(command: list[str], check: bool) -> subprocess.CompletedProcess[str]:
                self.assertTrue(check)
                package_dir = Path(command[command.index("--dest") + 1])
                (package_dir / "requests-2.32.5-py3-none-any.whl").write_bytes(b"root")
                (package_dir / "urllib3-2.5.0-py3-none-any.whl").write_bytes(b"dependency")
                return subprocess.CompletedProcess(command, 0)

            with mock.patch.object(download_package.subprocess, "run", side_effect=fake_run) as run:
                result = download_package.create_bundle(args)

            command = run.call_args.args[0]
            self.assertIn("requests[socks]==2.32.5", command)
            self.assertIn("--only-binary=:all:", command)
            self.assertNotIn("--no-deps", command)
            self.assertEqual(command[command.index("--python-version") + 1], "3.11")
            self.assertEqual(command[command.index("--abi") + 1], "cp311")
            self.assertEqual(result, output.resolve())
            self.assertEqual(
                (output / "requirements.txt").read_text(encoding="utf-8"),
                "requests[socks]==2.32.5\n",
            )
            self.assertIn("--no-index", (output / "install.ps1").read_text(encoding="utf-8"))
            self.assertIn("--no-index", (output / "install.sh").read_text(encoding="utf-8"))
            manifest = json.loads((output / "bundle-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["files"]), 2)
            self.assertEqual(manifest["target"]["requested_python_version"], "3.11.x")
            self.assertEqual(manifest["target"]["python_version"], "3.11")

    def test_allow_source_is_rejected_for_cross_target_bundle(self) -> None:
        args = download_package.parse_args(
            [
                "--package",
                "demo",
                "--version",
                "1.0",
                "--python-version",
                "3.12",
                "--allow-source",
            ]
        )
        with self.assertRaises(SystemExit) as error:
            download_package.build_download_command(args, "demo==1.0", Path("packages"))
        self.assertIn("matching target environment", str(error.exception))

    def test_rejects_unpinned_or_unsafe_input(self) -> None:
        with self.assertRaises(ValueError):
            download_package.validate_requirement("requests>=2", "2.32.5")
        with self.assertRaises(ValueError):
            download_package.validate_requirement("requests", "2.32.5;python_version<'4'")
        with self.assertRaises(ValueError):
            download_package.validate_requirement("requests", "latest")

    def test_prompts_for_package_and_lists_versions_without_downloading(self) -> None:
        query_result = subprocess.CompletedProcess(
            [],
            0,
            stdout="requests (2.32.5)\nAvailable versions: 2.32.5, 2.32.4\n",
            stderr="",
        )
        stdout = io.StringIO()
        with (
            mock.patch("builtins.input", return_value="requests") as prompt,
            mock.patch.object(
                download_package.subprocess, "run", return_value=query_result
            ) as run,
            redirect_stdout(stdout),
        ):
            result = download_package.main([])

        self.assertEqual(result, 0)
        prompt.assert_called_once_with("Dependency name: ")
        command = run.call_args.args[0]
        self.assertEqual(
            command[-5:],
            ["pip", "index", "versions", "--ignore-requires-python", "requests"],
        )
        self.assertNotIn("download", command)
        self.assertIn("Available versions: 2.32.5, 2.32.4", stdout.getvalue())
        self.assertIn("Target Python version is missing", stdout.getvalue())
        self.assertIn("No packages were downloaded", stdout.getvalue())

    def test_missing_python_never_runs_pip(self) -> None:
        stdout = io.StringIO()
        with (
            mock.patch.object(download_package.subprocess, "run") as run,
            redirect_stdout(stdout),
        ):
            result = download_package.main(
                ["--package", "requests", "--version", "2.32.5"]
            )

        self.assertEqual(result, 0)
        run.assert_not_called()
        self.assertIn("Target Python version is missing", stdout.getvalue())
        self.assertIn("No packages were downloaded", stdout.getvalue())

    def test_missing_package_version_lists_versions_without_downloading(self) -> None:
        query_result = subprocess.CompletedProcess(
            [], 0, stdout="Available versions: 2.32.5, 2.32.4\n", stderr=""
        )
        stdout = io.StringIO()
        with (
            mock.patch.object(
                download_package.subprocess, "run", return_value=query_result
            ) as run,
            redirect_stdout(stdout),
        ):
            result = download_package.main(
                ["--package", "requests", "--python-version", "3.11"]
            )

        self.assertEqual(result, 0)
        self.assertNotIn("download", run.call_args.args[0])
        self.assertIn("Available versions: 2.32.5, 2.32.4", stdout.getvalue())
        self.assertIn("No packages were downloaded", stdout.getvalue())

    def test_version_lookup_failure_does_not_download(self) -> None:
        query_result = subprocess.CompletedProcess(
            [],
            1,
            stdout="",
            stderr="ERROR: No matching distribution found for unknown-package",
        )
        stderr = io.StringIO()
        with (
            mock.patch.object(
                download_package.subprocess, "run", return_value=query_result
            ) as run,
            redirect_stderr(stderr),
        ):
            result = download_package.main(["--package", "unknown-package"])

        self.assertEqual(result, 2)
        self.assertNotIn("download", run.call_args.args[0])
        self.assertIn("Could not list versions", stderr.getvalue())

    def test_invalid_supplied_version_values_do_not_query_or_download(self) -> None:
        cases = (
            ["--package", "requests", "--version", "latest"],
            ["--package", "requests", "--python-version", "3.11.5"],
        )
        with mock.patch.object(download_package.subprocess, "run") as run:
            for arguments in cases:
                with self.subTest(arguments=arguments), redirect_stderr(io.StringIO()):
                    self.assertEqual(download_package.main(arguments), 2)
            run.assert_not_called()

    def test_requires_python_minor_version_line(self) -> None:
        with self.assertRaises(ValueError):
            download_package.validate_python_version("3")
        with self.assertRaises(ValueError):
            download_package.validate_python_version("3.11.5")
        self.assertEqual(download_package.validate_python_version("3.11"), (3, 11))
        self.assertEqual(download_package.validate_python_version("3.11.x"), (3, 11))
        self.assertEqual(download_package.normalized_python_version("3.11.X"), "3.11")

    def test_ambiguous_versions_never_run_pip(self) -> None:
        cases = (
            ["--package", "requests", "--version", "latest", "--python-version", "3.11"],
            ["--package", "requests", "--version", "2.32.5", "--python-version", "3.11.5"],
        )
        with mock.patch.object(download_package.subprocess, "run") as run:
            for arguments in cases:
                with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                    download_package.create_bundle(download_package.parse_args(arguments))
            run.assert_not_called()

    def test_default_output_includes_python_version(self) -> None:
        self.assertEqual(
            download_package.default_output("Pillow", "12.2.0", "3.11.x"),
            Path("output/python-offline-dependency-packager/Pillow-12.2.0-py3.11"),
        )

    def test_refuses_to_overwrite_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "bundle"
            output.mkdir()
            args = download_package.parse_args(
                [
                    "--package",
                    "requests",
                    "--version",
                    "2.32.5",
                    "--python-version",
                    "3.11",
                    "--output",
                    str(output),
                ]
            )
            with self.assertRaises(FileExistsError):
                download_package.create_bundle(args)


if __name__ == "__main__":
    unittest.main()
