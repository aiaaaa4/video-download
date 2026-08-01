import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PreflightQuestionnaireTest(unittest.TestCase):
    def test_questionnaire_contains_only_download_choices(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "skills/video-download/scripts/preflight.py")],
            capture_output=True,
            text=True,
            check=True,
        )
        text = result.stdout
        self.assertIn("下载质量", text)
        self.assertIn("去掉开头日期、结尾平台唯一编码", text)
        self.assertIn("确认默认设置", text)
        self.assertNotIn("翻译目标与交付", text)
        self.assertNotIn("外发处理", text)


if __name__ == "__main__":
    unittest.main()
