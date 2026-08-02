#!/usr/bin/env python3
"""Verify first-use dependencies and optionally probe one permitted media URL."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlsplit


def command_version(command: str, argument: str) -> str:
    executable = shutil.which(command)
    if not executable:
        raise SystemExit(f"ERROR: {command} is not installed or not on PATH")
    result = subprocess.run(
        [executable, argument], check=True, capture_output=True, text=True
    )
    return (result.stdout or result.stderr).splitlines()[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-dir", type=Path, default=Path.home() / "Desktop")
    parser.add_argument("--probe-url", help="optional permitted http(s) URL; no download is performed")
    args = parser.parse_args()

    parent = args.parent_dir.expanduser().resolve()
    if not parent.is_dir():
        raise SystemExit(f"ERROR: parent directory does not exist: {parent}")
    test_path = parent / ".video-download-write-test"
    try:
        test_path.touch(exist_ok=False)
        test_path.unlink()
    except OSError as error:
        raise SystemExit(f"ERROR: parent directory is not writable: {parent}: {error}") from error

    print(f"yt-dlp: {command_version('yt-dlp', '--version')}")
    print(f"ffmpeg: {command_version('ffmpeg', '-version')}")
    print(f"parent directory: {parent}")

    if args.probe_url:
        parsed = urlsplit(args.probe_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise SystemExit("ERROR: --probe-url must be an explicit http(s) URL")
        subprocess.run(
            ["yt-dlp", "--no-playlist", "--no-warnings", "-F", args.probe_url],
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
