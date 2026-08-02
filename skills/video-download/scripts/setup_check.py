#!/usr/bin/env python3
"""Manage the one-time video-download runtime check and yt-dlp update."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


def default_state_file() -> Path:
    override = os.environ.get("VIDEO_DOWNLOAD_STATE_DIR")
    if override:
        return Path(override).expanduser() / "first-use.json"
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "video-download" / "first-use.json"
    state_root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return state_root / "video-download" / "first-use.json"


def first_use_completed(path: Path) -> bool:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return state.get("schema_version") == 1 and state.get("completed") is True


def executable(name: str) -> str:
    value = shutil.which(name)
    if not value:
        raise SystemExit(f"ERROR: {name} is not installed or not on PATH")
    return value


def command_version(path: str, argument: str) -> str:
    result = subprocess.run(
        [path, argument], check=True, capture_output=True, text=True
    )
    return (result.stdout or result.stderr).splitlines()[0]


def update_yt_dlp(path: str) -> str:
    result = subprocess.run([path, "-U"], capture_output=True, text=True)
    detail = " ".join((result.stdout or result.stderr).split())
    if result.returncode == 0:
        return detail or "update check completed"
    lowered = detail.lower()
    if "package manager" in lowered or "brew" in lowered or "pip" in lowered:
        return f"externally managed; use its package manager ({detail})"
    return f"update attempt failed; current executable remains usable ({detail or 'unknown error'})"


def probe_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SystemExit("ERROR: --probe-url must be an explicit http(s) URL")
    subprocess.run(
        ["yt-dlp", "--no-playlist", "--no-warnings", "-F", url], check=True
    )


def write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def run_first_use(state_file: Path, media_url: str | None) -> int:
    if first_use_completed(state_file):
        print("video-download first-use check: already completed")
        return 0

    yt_dlp = executable("yt-dlp")
    ffmpeg = executable("ffmpeg")
    update_result = update_yt_dlp(yt_dlp)
    yt_dlp_version = command_version(yt_dlp, "--version")
    ffmpeg_version = command_version(ffmpeg, "-version")
    if media_url:
        probe_url(media_url)

    write_state(
        state_file,
        {
            "schema_version": 1,
            "completed": True,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "yt_dlp_version": yt_dlp_version,
            "yt_dlp_update": update_result,
            "ffmpeg_version": ffmpeg_version,
        },
    )
    print(f"yt-dlp: {yt_dlp_version}")
    print(f"yt-dlp update: {update_result}")
    print(f"ffmpeg: {ffmpeg_version}")
    print("video-download first-use check: completed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true", help="report whether first use is pending")
    parser.add_argument("--probe-url", help="optional permitted http(s) URL; no download is performed")
    parser.add_argument("--state-file", type=Path, default=default_state_file())
    args = parser.parse_args()

    if args.status:
        print("ready" if first_use_completed(args.state_file) else "first-use-required")
        return 0
    return run_first_use(args.state_file, args.probe_url)


if __name__ == "__main__":
    raise SystemExit(main())
