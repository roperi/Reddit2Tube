import logging
from pathlib import Path

from reddit2tube.database import VideoRepository
from reddit2tube.models import RunOptions
from reddit2tube.workflow import WorkflowDependencies, run_workflow


def test_download_only_workflow_marks_downloaded_video(settings, submission, tmp_path):
    calls = []

    def authenticate(*args):
        calls.append("reddit-auth")
        return object()

    def get_submissions(*args):
        return [submission]

    def download(url, title, *, download_dir):
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
    def download(url, title, *, download_dir):
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

    def download(url, title, *, download_dir):
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
