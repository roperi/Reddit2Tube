import logging
from dataclasses import replace
from pathlib import Path

import pytest

from reddit2tube.database import VideoRepository
from reddit2tube.downloader import get_download_options
from reddit2tube.models import RunOptions
from reddit2tube.workflow import WorkflowDependencies, retry_pending_uploads, run_workflow


@pytest.mark.parametrize("cookie_source", ["browser", "file", "none"])
def test_workflow_uses_cookie_settings(settings, submission, monkeypatch, tmp_path, cookie_source):
    monkeypatch.setenv("REDDIT_COOKIES_FROM_BROWSER", "chrome")
    monkeypatch.delenv("REDDIT_COOKIES_FILE", raising=False)
    expected = {}
    if cookie_source == "browser":
        settings = replace(settings, reddit_cookies_from_browser="firefox")
        expected = {"cookiesfrombrowser": ("firefox",)}
    elif cookie_source == "file":
        cookie_file = tmp_path / "cookies.txt"
        cookie_file.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
        settings = replace(settings, reddit_cookies_file=cookie_file)
        expected = {"cookiefile": str(cookie_file)}
    received = []

    def download(url, title, *, download_dir, env):
        options = get_download_options(download_dir=download_dir, env=env)
        received.append({key: value for key, value in options.items() if key != "outtmpl"})
        return Path(download_dir) / "video.mp4"

    summary = run_workflow(
        settings,
        RunOptions("cats", just_download=True),
        dependencies=WorkflowDependencies(
            authenticate_reddit=lambda *args: object(),
            get_top_submissions=lambda *args: [submission],
            download_video=download,
        ),
    )
    assert summary.downloaded == 1
    assert summary.failures == 0
    assert received == [expected]


def test_download_only_workflow_marks_downloaded_video(settings, submission, tmp_path):
    calls = []

    def authenticate(*args):
        calls.append("reddit-auth")
        return object()

    def get_submissions(*args):
        return [submission]

    def download(url, title, *, download_dir, env):
        calls.append((url, title, download_dir))
        path = Path(download_dir) / "video.mp4"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"video")
        return path

    dependencies = WorkflowDependencies(
        authenticate_reddit=authenticate,
        get_top_submissions=get_submissions,
        download_video=download,
    )
    summary = run_workflow(
        settings,
        RunOptions("cats", just_download=True),
        dependencies=dependencies,
        logger=logging.getLogger("test"),
    )
    assert summary.examined == 1
    assert summary.downloaded == 1
    assert summary.uploaded == 0
    assert summary.failures == 0
    assert "reddit-auth" in calls
    assert not VideoRepository(settings.database_file).contains("abc123")


def test_upload_failure_does_not_mark_video(settings, submission):
    def download(url, title, *, download_dir, env):
        return Path(download_dir) / "video.mp4"

    dependencies = WorkflowDependencies(
        authenticate_reddit=lambda *args: object(),
        get_top_submissions=lambda *args: [submission],
        download_video=download,
        get_authenticated_service=lambda settings: object(),
        initialize_upload=lambda *args: (_ for _ in ()).throw(RuntimeError("upload failed")),
    )
    summary = run_workflow(
        settings,
        RunOptions("cats"),
        dependencies=dependencies,
        logger=logging.getLogger("test"),
    )
    assert summary.failures == 1
    assert summary.uploaded == 0
    assert not VideoRepository(settings.database_file).contains("abc123")


def test_non_video_and_duplicate_submissions_are_skipped(settings, submission):
    from types import SimpleNamespace

    duplicate = SimpleNamespace(**submission.__dict__)
    duplicate.id = "duplicate"
    duplicate.url = "https://v.redd.it/video"
    repository = VideoRepository(settings.database_file)
    repository.mark_uploaded("duplicate", "Already done")
    non_video = SimpleNamespace(**submission.__dict__)
    non_video.id = "text"
    non_video.url = "https://example.com/image"
    dependencies = WorkflowDependencies(
        authenticate_reddit=lambda *args: object(),
        get_top_submissions=lambda *args: [duplicate, non_video],
        download_video=lambda *args, **kwargs: Path("video.mp4"),
    )
    summary = run_workflow(
        settings,
        RunOptions("cats", just_download=True),
        dependencies=dependencies,
        logger=logging.getLogger("test"),
    )
    assert summary.skipped_uploaded == 1
    assert summary.skipped_non_video == 1


def test_troubleshooting_profile_forces_private(settings, submission, monkeypatch):
    calls = []

    def download(url, title, *, download_dir, env):
        path = Path(download_dir) / "video.mp4"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"video")
        return path

    monkeypatch.setattr(
        "reddit2tube.workflow.inspect_media",
        lambda path, **kwargs: type(
            "Info",
            (),
            {
                "duration": 30.0,
                "width": 720,
                "height": 1280,
                "video_codec": "h264",
                "audio_codec": "aac",
                "size": 5,
                "is_likely_short": False,
            },
        )(),
    )

    def upload(*args):
        calls.append(args[2])
        return "youtube-id"

    dependencies = WorkflowDependencies(
        authenticate_reddit=lambda *args: object(),
        get_top_submissions=lambda *args: [submission],
        download_video=download,
        get_authenticated_service=lambda settings: object(),
        initialize_upload=upload,
    )
    summary = run_workflow(
        settings,
        RunOptions("cats", privacy_status="public", troubleshooting_upload=True),
        dependencies=dependencies,
        logger=logging.getLogger("test"),
    )
    assert summary.uploaded == 1
    assert calls == ["private"]


def test_upload_failure_records_pending(settings, submission):
    def download(url, title, *, download_dir, env):
        path = Path(download_dir) / "video.mp4"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"video")
        return path

    dependencies = WorkflowDependencies(
        authenticate_reddit=lambda *args: object(),
        get_top_submissions=lambda *args: [submission],
        download_video=download,
        get_authenticated_service=lambda settings: object(),
        initialize_upload=lambda *args: (_ for _ in ()).throw(RuntimeError("upload failed")),
    )
    summary = run_workflow(
        settings,
        RunOptions("cats"),
        dependencies=dependencies,
        logger=logging.getLogger("test"),
    )
    assert summary.failures == 1
    rows = VideoRepository(settings.database_file).pending_uploads()
    assert [row.submission_id for row in rows] == ["abc123"]
    assert rows[0].media_path.endswith("video.mp4")
    assert rows[0].attempts == 1
    assert "upload failed" in rows[0].last_error


def test_successful_upload_clears_pending(settings, submission):
    def download(url, title, *, download_dir, env):
        path = Path(download_dir) / "video.mp4"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"video")
        return path

    repository = VideoRepository(settings.database_file)
    dependencies = WorkflowDependencies(
        authenticate_reddit=lambda *args: object(),
        get_top_submissions=lambda *args: [submission],
        download_video=download,
        get_authenticated_service=lambda settings: object(),
        initialize_upload=lambda *args: "youtube-id",
    )
    summary = run_workflow(
        settings,
        RunOptions("cats"),
        dependencies=dependencies,
        logger=logging.getLogger("test"),
    )
    assert summary.uploaded == 1
    assert repository.pending_uploads() == []
    assert repository.contains("abc123")


def test_retry_pending_uploads_reuses_local_file(settings):
    repository = VideoRepository(settings.database_file)
    media = settings.download_dir / "video.mp4"
    media.parent.mkdir(parents=True, exist_ok=True)
    media.write_bytes(b"video")
    repository.record_pending("abc123", "Title", "Description", "https://reddit/abc", str(media))
    uploads = []

    def upload(youtube, options, privacy, made_for_kids):
        uploads.append((options["title"], options["file"]))
        return "youtube-id"

    dependencies = WorkflowDependencies(
        download_video=lambda *args, **kwargs: pytest.fail("should not re-download"),
        get_authenticated_service=lambda settings: object(),
        initialize_upload=upload,
    )
    summary = retry_pending_uploads(
        settings,
        RunOptions("cats"),
        dependencies=dependencies,
        logger=logging.getLogger("test"),
    )
    assert summary.uploaded == 1
    assert summary.downloaded == 0
    assert uploads == [("Title", media)]
    assert repository.pending_uploads() == []
    assert repository.contains("abc123")


def test_retry_pending_uploads_redownloads_when_missing(settings):
    repository = VideoRepository(settings.database_file)
    repository.record_pending(
        "abc123",
        "Title",
        "Description",
        "https://reddit/abc",
        str(settings.download_dir / "gone.mp4"),
    )
    downloads = []

    def download(url, title, *, download_dir, env):
        downloads.append((url, title))
        path = Path(download_dir) / "video.mp4"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"video")
        return path

    dependencies = WorkflowDependencies(
        download_video=download,
        get_authenticated_service=lambda settings: object(),
        initialize_upload=lambda *args: "youtube-id",
    )
    summary = retry_pending_uploads(
        settings,
        RunOptions("cats"),
        dependencies=dependencies,
        logger=logging.getLogger("test"),
    )
    assert downloads == [("https://reddit/abc", "Title")]
    assert summary.downloaded == 1
    assert summary.uploaded == 1
    assert repository.pending_uploads() == []


def test_retry_upload_failure_keeps_pending(settings):
    repository = VideoRepository(settings.database_file)
    media = settings.download_dir / "video.mp4"
    media.parent.mkdir(parents=True, exist_ok=True)
    media.write_bytes(b"video")
    repository.record_pending("abc123", "Title", "Description", "https://reddit/abc", str(media))
    dependencies = WorkflowDependencies(
        get_authenticated_service=lambda settings: object(),
        initialize_upload=lambda *args: (_ for _ in ()).throw(RuntimeError("still broken")),
    )
    summary = retry_pending_uploads(
        settings,
        RunOptions("cats"),
        dependencies=dependencies,
        logger=logging.getLogger("test"),
    )
    assert summary.failures == 1
    rows = repository.pending_uploads()
    assert len(rows) == 1
    assert rows[0].attempts == 1
    assert "still broken" in rows[0].last_error


def test_retry_skips_submissions_already_uploaded(settings):
    repository = VideoRepository(settings.database_file)
    repository.mark_uploaded("abc123", "Title", "youtube-id")
    repository.record_pending("abc123", "Title", "Description", "https://reddit/abc")
    dependencies = WorkflowDependencies(
        get_authenticated_service=lambda settings: pytest.fail("should not authenticate"),
    )
    summary = retry_pending_uploads(
        settings,
        RunOptions("cats"),
        dependencies=dependencies,
        logger=logging.getLogger("test"),
    )
    assert summary.skipped_uploaded == 1
    assert summary.uploaded == 0
    assert repository.pending_uploads() == []


def test_retry_rejects_download_only_mode(settings):
    with pytest.raises(ValueError):
        retry_pending_uploads(
            settings,
            RunOptions("cats", just_download=True),
            logger=logging.getLogger("test"),
        )
