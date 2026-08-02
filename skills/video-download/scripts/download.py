#!/usr/bin/env python3
"""Execute a reviewed single-video download into a new media project."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def prepare_parent(path: Path) -> Path:
    parent = path.expanduser().resolve()
    try:
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=parent, prefix=".video-download-write-", delete=True
        ):
            pass
    except OSError as error:
        fail(f"confirmed parent directory is not writable: {parent}: {error}")
    return parent


def safe_name(value: str) -> str:
    value = re.sub(r"[\x00-\x1f\x7f]+", " ", value)
    value = re.sub(r"[\\/:*?\"<>|]", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    if not value or value in {".", ".."}:
        fail("the media name must not be empty")
    return value[:160].rstrip(" .")


def default_media_name(info: dict) -> str:
    raw_title = str(info.get("title") or "")
    if not raw_title:
        fail("the platform did not expose a title; provide --name")
    title = safe_name(raw_title)
    raw_date = str(info.get("upload_date") or info.get("release_date") or "")
    date = (
        f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
        if re.fullmatch(r"\d{8}", raw_date)
        else ""
    )
    raw_video_id = str(info.get("id") or "")
    video_id = f"[{safe_name(raw_video_id)}]" if raw_video_id else ""
    return safe_name(" ".join(part for part in (title, date, video_id) if part))


def probe(url: str) -> dict:
    command = ["yt-dlp", "--dump-single-json", "--no-warnings", "--no-playlist"]
    command.append(url)
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        fail(f"yt-dlp returned invalid probe JSON: {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="explicit http(s) media URL")
    parser.add_argument("--parent-dir", required=True, type=Path)
    parser.add_argument(
        "--name",
        help="confirmed custom name; otherwise use original title, platform date, and video ID",
    )
    parser.add_argument("--video-format", required=True, help="reviewed video-only selector")
    parser.add_argument(
        "--video-audio-format",
        required=True,
        help="reviewed best playback audio selector for the merged video",
    )
    parser.add_argument(
        "--asr-audio-format", required=True, help="reviewed best ASR audio selector"
    )
    parser.add_argument("--source-lang", help="one confirmed original subtitle language code")
    parser.add_argument("--subtitle-kind", choices=("none", "manual", "auto"), default="none")
    parser.add_argument("--merge-format", choices=("mkv", "mp4"), default="mkv")
    args = parser.parse_args()

    parsed = urlsplit(args.url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        fail("only an explicit http:// or https:// URL is accepted")
    if not shutil.which("yt-dlp") or not shutil.which("ffmpeg"):
        fail("yt-dlp and ffmpeg must both be installed")
    if args.subtitle_kind != "none" and not args.source_lang:
        fail("--source-lang is required when downloading a subtitle")

    parent_dir = prepare_parent(args.parent_dir)
    info = probe(args.url)
    media_name = safe_name(args.name) if args.name else default_media_name(info)
    project_dir = parent_dir / media_name
    if project_dir.exists():
        fail(f"project directory already exists; choose a new parent or title: {project_dir}")
    input_dir = project_dir / ".work" / "input"
    input_dir.mkdir(parents=True)

    common = ["yt-dlp", "--windows-filenames", "--no-playlist", "--no-keep-video"]
    run(
        common
        + [
            "--no-overwrites",
            "--write-thumbnail",
            "--convert-thumbnails",
            "png",
            "-o",
            f"thumbnail:{project_dir / '原始封面.%(ext)s'}",
            "-f",
            f"{args.video_format}+{args.video_audio_format}",
            "--merge-output-format",
            args.merge_format,
            "-o",
            str(project_dir / f"{media_name}.%(ext)s"),
            args.url,
        ]
    )
    run(
        common
        + [
            "-f",
            args.asr_audio_format,
            "-P",
            str(input_dir),
            "-o",
            f"{media_name}.%(ext)s",
            args.url,
        ]
    )

    if args.subtitle_kind != "none":
        flags = "--write-subs" if args.subtitle_kind == "manual" else "--write-auto-subs"
        run(
            common
            + [
                "--skip-download",
                flags,
                "--sub-langs",
                args.source_lang,
                "--sub-format",
                "srt/vtt/best",
                "--convert-subs",
                "srt",
                "-P",
                str(input_dir),
                "-o",
                f"subtitle:{media_name}.原语言字幕.%(ext)s",
                args.url,
            ]
        )

    video_files = [
        path
        for path in project_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".avif"}
        and not path.name.endswith(".part")
    ]
    audio_files = [
        path
        for path in input_dir.iterdir()
        if path.is_file()
        and path.name.startswith(f"{media_name}.")
        and "原语言字幕" not in path.name
        and not path.name.endswith(".part")
    ]
    subtitle_files = [
        path
        for path in input_dir.iterdir()
        if path.is_file()
        and path.name.startswith(f"{media_name}.原语言字幕")
        and path.suffix.lower() == ".srt"
    ]
    if len(video_files) != 1:
        fail(f"expected exactly one downloaded video, found {len(video_files)}")
    if len(audio_files) != 1:
        fail(f"expected exactly one ASR audio file, found {len(audio_files)}")
    if args.subtitle_kind != "none" and len(subtitle_files) != 1:
        fail("the selected source-language subtitle was not created")

    cover = project_dir / "原始封面.png"
    print(
        json.dumps(
            {
                "project_dir": str(project_dir),
                "video": str(video_files[0]),
                "asr_audio": str(audio_files[0]),
                "source_subtitle": str(subtitle_files[0]) if subtitle_files else None,
                "original_thumbnail": str(cover) if cover.is_file() else None,
                "formats": {
                    "video": args.video_format,
                    "video_audio": args.video_audio_format,
                    "asr_audio": args.asr_audio_format,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
