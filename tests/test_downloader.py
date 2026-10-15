from pathlib import Path

import pytest

from reddit2tube.downloader import (
    download_video,
    get_download_options,
    is_reddit_metadata_error,
    safe_filename,
)
from reddit2tube.media import MediaInfo


def test_safe_filename_removes_path_and_special_characters():
    name = safe_filename("../../a video: *great*?")
    assert "/" not in name
    assert ".." not in name
    assert name


def test_cookie_options_are_mutually_exclusive(tmp_path):
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text("cookies", encoding="utf-8")
    with pytest.raises(ValueError, match="only one"):
        get_download_options(
            env={
                "REDDIT_COOKIES_FROM_BROWSER": "firefox",
                "REDDIT_COOKIES_FILE": str(cookie_file),
            }
        )


def test_browser_cookie_option_is_forwarded(tmp_path):
    options = get_download_options(
        download_dir=tmp_path, env={"REDDIT_COOKIES_FROM_BROWSER": "firefox"}
    )
    assert options["cookiesfrombrowser"] == ("firefox",)


def test_missing_cookie_file_is_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        get_download_options(
            download_dir=tmp_path,
            env={"REDDIT_COOKIES_FILE": str(tmp_path / "missing.txt")},
        )


def test_explicit_empty_env_does_not_use_process_cookies(monkeypatch):
    monkeypatch.setenv("REDDIT_COOKIES_FROM_BROWSER", "firefox")
    monkeypatch.setenv("REDDIT_COOKIES_FILE", "/missing/cookies.txt")
    options = get_download_options(env={})
    assert "cookiesfrombrowser" not in options
    assert "cookiefile" not in options


def test_authentication_error_explains_application_cookie_settings(monkeypatch, tmp_path):
    import yt_dlp

    original = yt_dlp.utils.DownloadError(
        "ERROR: [Reddit] 1x3xqhv: Account authentication is required."
    )

    def fail(*args, **kwargs):
        raise original

    monkeypatch.setattr(yt_dlp.YoutubeDL, "extract_info", fail)
    with pytest.raises(RuntimeError, match="REDDIT_COOKIES_FROM_BROWSER") as caught:
        download_video("https://www.reddit.com/test", "test", download_dir=tmp_path, env={})
    assert "REDDIT_COOKIES_FILE" in str(caught.value)
    assert caught.value.__cause__ is original


def test_metadata_error_detection():
    assert is_reddit_metadata_error(RuntimeError("Unable to download JSON metadata"))
    assert not is_reddit_metadata_error(RuntimeError("disk full"))


def test_media_info_identifies_likely_short():
    info = MediaInfo(Path("video.mp4"), 30, 720, 1280, "h264", "aac", 100)
    assert info.is_likely_short
    landscape = MediaInfo(Path("video.mp4"), 30, 1280, 720, "h264", "aac", 100)
    assert not landscape.is_likely_short
