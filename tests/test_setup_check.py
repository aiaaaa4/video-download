from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "setup_check", ROOT / "skills/video-download/scripts/setup_check.py"
)
assert SPEC and SPEC.loader
setup_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup_check)


class SetupCheckTests(unittest.TestCase):
    def test_first_use_checks_only_runtime_dependency_versions(self) -> None:
        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            output = "2026.07.04\n" if command[1] == "--version" else "ffmpeg version 8.1.2\n"
            return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

        with (
            mock.patch.object(sys, "argv", ["setup_check.py"]),
            mock.patch.object(setup_check.shutil, "which", side_effect=lambda name: f"/bin/{name}"),
            mock.patch.object(setup_check.subprocess, "run", side_effect=fake_run),
            mock.patch("builtins.print") as print_mock,
        ):
            self.assertEqual(setup_check.main(), 0)

        output = [call.args[0] for call in print_mock.call_args_list]
        self.assertEqual(output, ["yt-dlp: 2026.07.04", "ffmpeg: ffmpeg version 8.1.2"])
        self.assertTrue(all("parent" not in line.lower() for line in output))


if __name__ == "__main__":
    unittest.main()
