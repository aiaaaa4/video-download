#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re


def safe_field(value: str) -> str:
    return re.sub(r"[\x00-\x1f\x7f]+", " ", value).strip()[:240]


def questionnaire(video_options: list[str], default_name: str, source_language: str) -> str:
    options = "\n".join(
        f"   {index}. {safe_field(option)}"
        for index, option in enumerate(video_options, start=1)
    )
    language = safe_field(source_language) if source_language else "尚未可靠识别"
    return f"""准备下载目标链接的视频和配套素材。已完成格式探测，开始下载前请一次性确认：
1. 内容授权：请确认你有权下载或使用这个媒体。
2. 下载清单：视频文件 1 份保存在项目根目录；ASR 校对音频 1 份、原语言字幕 1 份（如有，默认 SRT）、原始封面图 1 份（如有，默认平台最高质量并转为 PNG）作为配套素材，保存在项目的 .work/input/ 中。另行下载的播放音频只用于与视频流合并，合并成功后与临时纯视频流一并删除；ASR 校对音频独立选择最适合转写的最高质量源音频。
3. 视频质量：默认选择第 1 项，即最高可用 SDR 兼容方案。实际可用选项如下；每项应包含分辨率、编码、容器和可见的估算大小：
{options}
4. 文件命名：默认名称为“{safe_field(default_name)}”，顺序是原语言真实标题、平台日期、尾部视频 ID。用户也可以提供自定义名称；自定义名称会同时用于项目文件夹、视频、ASR 校对音频和原语言字幕。
5. 保存位置：默认桌面；也可以提供其他父目录。下载时会在目标位置自动创建新的独立项目文件夹，不把文件散落到已有目录。
6. 视频源语言：当前识别为“{language}”。如不正确或尚未可靠识别，请提供实际语言。原语言字幕人工字幕优先；没有人工字幕时才使用自动字幕，平台没有时不生成。
7. 播放列表：默认只下载当前视频，不下载整个播放列表；只有明确要求时才处理播放列表。

如接受以上默认设置，请回复：确认默认设置，并确认有权下载。"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--video-option",
        action="append",
        required=True,
        help="reviewed technical option; pass the highest SDR option first",
    )
    parser.add_argument("--default-name", required=True)
    parser.add_argument("--source-language", default="")
    args = parser.parse_args()
    print(questionnaire(args.video_option, args.default_name, args.source_language))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
