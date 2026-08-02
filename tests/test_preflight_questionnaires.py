import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PreflightQuestionnaireTest(unittest.TestCase):
    def test_questionnaire_contains_only_download_choices(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "skills/video-download/scripts/preflight.py"),
                "--video-option",
                "2160p SDR, H.264/AAC, MP4, 1.2 GiB",
                "--video-option",
                "1080p SDR, H.264/AAC, MP4, 420 MiB",
                "--default-name",
                "Lezione italiana 2026-08-02 [abc123]",
                "--source-language",
                "意大利语 (it)",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        text = result.stdout
        self.assertIn("视频质量", text)
        self.assertIn("2160p SDR", text)
        self.assertIn("Lezione italiana 2026-08-02 [abc123]", text)
        self.assertIn("意大利语 (it)", text)
        self.assertIn("最适合 ASR 转写的最佳音频", text)
        self.assertIn("自动创建新的独立项目文件夹", text)
        self.assertIn("确认默认设置", text)
        self.assertNotIn("翻译目标与交付", text)
        self.assertNotIn("外发处理", text)


if __name__ == "__main__":
    unittest.main()
