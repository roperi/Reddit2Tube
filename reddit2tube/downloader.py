"""yt-dlp integration and safe local download handling."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path


def safe_filename(value: str, max_length: int = 120) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", value).strip(" .")
    cleaned = re.sub(r"\.{2,}", "_", cleaned)
    return (cleaned or "reddit-video")[:max_length]


def get_download_options(
    *, download_dir: str | Path = "/tmp/reddit2tube", env: Mapping[str, str] | None = None
) -> dict:
    values = env or os.environ
    browser = values.get("REDDIT_COOKIES_FROM_BROWSER")
    cookie_file = values.get("REDDIT_COOKIES_FILE")
    if browser and cookie_file:
        raise ValueError("Set only one of REDDIT_COOKIES_FROM_BROWSER or REDDIT_COOKIES_FILE.")
    directory = Path(download_dir).expanduser()
    options = {"outtmpl": str(directory / "%(title)s.%(ext)s")}
    if browser:
        options["cookiesfrombrowser"] = tuple(browser.split(":", 1))
    elif cookie_file:
        path = Path(cookie_file).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Reddit cookie file does not exist: {path}")
        options["cookiefile"] = str(path)
    return options


def is_reddit_metadata_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(
        marker in message
        for marker in (
            "failed to parse json",
            "unable to download json metadata",
            "account authentication is required",
        )
    )


def download_video(
    video_url: str,
    video_title: str,
    *,
    download_dir: str | Path = "/tmp/reddit2tube",
    env: Mapping[str, str] | None = None,
) -> Path:
    import yt_dlp

    directory = Path(download_dir).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    options = get_download_options(download_dir=directory, env=env)
    options["outtmpl"] = str(directory / f"{safe_filename(video_title)}.%(ext)s")
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(video_url, download=True)
            return Path(ydl.prepare_filename(info))
    except yt_dlp.utils.DownloadError as error:
        if is_reddit_metadata_error(error):
            raise RuntimeError(
                "Reddit blocked the metadata request or returned an anti-bot challenge. "
                "Upgrade yt-dlp or configure Reddit browser cookies."
            ) from error
        raise
