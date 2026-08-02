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
        self.assertIn("1. 内容授权", text)
        self.assertIn("2. 下载清单", text)
        self.assertIn("3. 视频质量", text)
        self.assertIn("4. 文件命名", text)
        self.assertIn("5. 保存位置", text)
        self.assertIn("6. 视频源语言", text)
        self.assertIn("7. 播放列表", text)
        self.assertIn("2160p SDR", text)
        self.assertIn("Lezione italiana 2026-08-02 [abc123]", text)
        self.assertIn("意大利语 (it)", text)
        self.assertIn("最适合转写的最高质量源音频", text)
        self.assertIn("视频文件 1 份", text)
        self.assertIn("ASR 校对音频 1 份", text)
        self.assertIn("合并成功后与临时纯视频流一并删除", text)
        self.assertIn("默认 SRT", text)
        self.assertIn("默认平台最高质量并转为 PNG", text)
        self.assertIn(".work/input/", text)
        self.assertIn("自动创建新的独立项目文件夹", text)
        self.assertIn("确认默认设置", text)
        self.assertNotIn("翻译目标与交付", text)
        self.assertNotIn("外发处理", text)


if __name__ == "__main__":
    unittest.main()
