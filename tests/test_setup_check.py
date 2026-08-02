from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
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
    def test_skill_contract_has_exact_user_entry_messages(self) -> None:
        source = (ROOT / "skills/video-download/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("直接发送下载链接即可。", source)
        self.assertIn(
            "首次使用video-download skill，我将执行一次依赖/环境检查和更新，后续任务将跳过此步骤。",
            source,
        )
        self.assertIn("python scripts/setup_check.py --status", source)
        self.assertIn("installed versions of both yt-dlp and FFmpeg", source)

    def test_status_reports_first_use_then_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "first-use.json"
            with (
                mock.patch.object(
                    sys, "argv", ["setup_check.py", "--status", "--state-file", str(state_file)]
                ),
                mock.patch("builtins.print") as print_mock,
            ):
                self.assertEqual(setup_check.main(), 0)
                print_mock.assert_called_once_with("first-use-required")

            setup_check.write_state(state_file, {"schema_version": 1, "completed": True})
            with (
                mock.patch.object(
                    sys, "argv", ["setup_check.py", "--status", "--state-file", str(state_file)]
                ),
                mock.patch("builtins.print") as print_mock,
            ):
                self.assertEqual(setup_check.main(), 0)
                print_mock.assert_called_once_with("ready")

    def test_first_use_updates_checks_and_persists_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "first-use.json"

            def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                if command[1] == "-U":
                    return subprocess.CompletedProcess(command, 0, stdout="yt-dlp is up to date\n", stderr="")
                output = "2026.07.04\n" if command[1] == "--version" else "ffmpeg version 8.1.2\n"
                return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

            argv = ["setup_check.py", "--state-file", str(state_file)]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(setup_check.shutil, "which", side_effect=lambda name: f"/bin/{name}"),
                mock.patch.object(setup_check.subprocess, "run", side_effect=fake_run),
                mock.patch("builtins.print") as print_mock,
            ):
                self.assertEqual(setup_check.main(), 0)

            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertTrue(state["completed"])
            self.assertEqual(state["yt_dlp_version"], "2026.07.04")
            self.assertEqual(state["ffmpeg_version"], "ffmpeg version 8.1.2")
            output = [call.args[0] for call in print_mock.call_args_list]
            self.assertIn("yt-dlp: 2026.07.04", output)
            self.assertIn("ffmpeg: ffmpeg version 8.1.2", output)
            self.assertIn("completed", print_mock.call_args_list[-1].args[0])

            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(setup_check, "update_yt_dlp") as update_mock,
                mock.patch("builtins.print") as print_mock,
            ):
                self.assertEqual(setup_check.main(), 0)
                update_mock.assert_not_called()
                print_mock.assert_called_once_with(
                    "video-download first-use check: already completed"
                )

    def test_external_package_manager_update_is_nonfatal(self) -> None:
        result = subprocess.CompletedProcess(
            ["yt-dlp", "-U"],
            100,
            stdout="ERROR: use your package manager to update yt-dlp\n",
            stderr="",
        )
        with mock.patch.object(setup_check.subprocess, "run", return_value=result):
            detail = setup_check.update_yt_dlp("yt-dlp")
        self.assertIn("externally managed", detail)

    def test_failed_dependency_check_does_not_mark_first_use_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "first-use.json"
            with mock.patch.object(setup_check.shutil, "which", return_value=None):
                with self.assertRaises(SystemExit):
                    setup_check.run_first_use(state_file, None)
            self.assertFalse(state_file.exists())


if __name__ == "__main__":
    unittest.main()
