from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
