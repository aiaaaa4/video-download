from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "download", ROOT / "skills/video-download/scripts/download.py"
)
assert SPEC and SPEC.loader
download = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(download)


class DownloadScriptTests(unittest.TestCase):
    def test_safe_name_removes_path_controls(self) -> None:
        self.assertEqual(download.safe_name("  2026: A/B? lesson  "), "2026 A B lesson")
        with self.assertRaises(SystemExit):
            download.safe_name("../")

    def test_default_name_keeps_original_title_date_and_id_in_order(self) -> None:
        self.assertEqual(
            download.default_media_name(
                {"title": "Lezione italiana", "upload_date": "20260802", "id": "abc123"}
            ),
            "Lezione italiana 2026-08-02 [abc123]",
        )

    def test_default_name_omits_unavailable_date_and_id(self) -> None:
        self.assertEqual(download.default_media_name({"title": "日本語の授業"}), "日本語の授業")

    def test_default_name_requires_platform_title(self) -> None:
        with self.assertRaises(SystemExit):
            download.default_media_name({"id": "abc123"})

    def test_prepare_parent_runs_at_task_time_and_cleans_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "new-parent"
            self.assertEqual(download.prepare_parent(parent), parent.resolve())
            self.assertTrue(parent.is_dir())
            self.assertEqual(list(parent.glob(".video-download-write-*")), [])

    def test_main_creates_one_deterministic_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            commands: list[list[str]] = []
            metadata = {
                "title": "Lezione italiana",
                "upload_date": "20260802",
                "id": "abc123",
            }

            def fake_run(command: list[str]) -> None:
                commands.append(command)
                project = parent / "Lezione italiana 2026-08-02 [abc123]"
                input_dir = project / ".work" / "input"
                if "--write-thumbnail" in command:
                    output = Path(command[command.index("-o", command.index("-f")) + 1])
                    output.with_suffix(".mp4").write_bytes(b"video source")
                    (input_dir / "原始封面.png").write_bytes(b"cover")
                elif "--skip-download" in command:
                    (input_dir / "Lezione italiana 2026-08-02 [abc123].原语言字幕.it.srt").write_text(
                        "subtitle", encoding="utf-8"
                    )
                elif command[0] == "ffmpeg":
                    Path(command[-1]).write_bytes(b"merged video")
                    (project / ".DS_Store").write_bytes(b"finder metadata")
                elif "播放音频" in command[command.index("-o") + 1]:
                    (input_dir / "Lezione italiana 2026-08-02 [abc123].播放音频.m4a").write_bytes(
                        b"playback audio"
                    )
                else:
                    (input_dir / "Lezione italiana 2026-08-02 [abc123].ASR音频.opus").write_bytes(
                        b"ASR audio"
                    )

            argv = [
                "download.py",
                "https://example.com/watch?v=abc123",
                "--parent-dir",
                str(parent),
                "--video-format",
                "137",
                "--video-audio-format",
                "140",
                "--asr-audio-format",
                "251",
                "--source-lang",
                "it",
                "--subtitle-kind",
                "manual",
                "--merge-format",
                "mp4",
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(download.shutil, "which", return_value="/usr/bin/tool"),
                mock.patch.object(download, "probe", return_value=metadata),
                mock.patch.object(download, "run", side_effect=fake_run),
                mock.patch("builtins.print") as print_mock,
            ):
                self.assertEqual(download.main(), 0)

            report = json.loads(print_mock.call_args.args[0])
            self.assertTrue(Path(report["video"]).is_file())
            self.assertTrue(Path(report["playback_audio"]).is_file())
            self.assertTrue(Path(report["asr_audio"]).is_file())
            self.assertTrue(Path(report["source_subtitle"]).is_file())
            self.assertTrue(Path(report["original_thumbnail"]).is_file())
            self.assertEqual(report["formats"]["video"], "137")
            self.assertEqual(report["formats"]["video_audio"], "140")
            self.assertEqual(report["formats"]["asr_audio"], "251")
            self.assertEqual(commands[0][commands[0].index("-f") + 1], "137")
            self.assertEqual(commands[1][commands[1].index("-f") + 1], "140")
            self.assertIn(".播放音频.%(ext)s", commands[1][commands[1].index("-o") + 1])
            self.assertEqual(commands[2][0], "ffmpeg")
            self.assertEqual(commands[3][commands[3].index("-f") + 1], "251")
            self.assertIn(".ASR音频.%(ext)s", commands[3][commands[3].index("-o") + 1])
            project = parent / "Lezione italiana 2026-08-02 [abc123]"
            root_media = [
                path
                for path in project.iterdir()
                if path.is_file() and path.suffix.lower() in {".mp4", ".mkv"}
            ]
            self.assertEqual(len(root_media), 1)
            input_files = [path for path in (project / ".work" / "input").iterdir() if path.is_file()]
            self.assertEqual(len(input_files), 4)


if __name__ == "__main__":
    unittest.main()
