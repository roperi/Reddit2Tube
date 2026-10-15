def test_repository_initializes_and_is_idempotent(tmp_path):
    from reddit2tube.database import VideoRepository

    repository = VideoRepository(tmp_path / "nested" / "videos.sqlite3")
    repository.initialize()
    assert not repository.contains("abc")
    repository.mark_uploaded("abc", "A title", "youtube-id")
    repository.mark_uploaded("abc", "A title", "youtube-id")
    assert repository.contains("abc")


def test_repository_enforces_daily_upload_attempt_limit(tmp_path):
    from datetime import datetime, timezone

    from reddit2tube.database import VideoRepository

    repository = VideoRepository(tmp_path / "videos.sqlite3")
    day = datetime(2026, 9, 3, tzinfo=timezone.utc)
    assert [repository.reserve_upload_attempt(2, now=day) for _ in range(3)] == [True, True, False]
    assert repository.reserve_upload_attempt(2, now=day.replace(day=4))


def test_repository_tracks_pending_uploads(tmp_path):
    from reddit2tube.database import VideoRepository

    repository = VideoRepository(tmp_path / "videos.sqlite3")
    assert repository.pending_uploads() == []

    repository.record_pending("abc", "Title", "Description", "https://reddit.example/abc")
    rows = repository.pending_uploads()
    assert [row.submission_id for row in rows] == ["abc"]
    assert rows[0].media_path is None
    assert rows[0].attempts == 0

    repository.record_failure("abc", "connection reset")
    repository.set_pending_media("abc", "/tmp/abc.mp4")
    rows = repository.pending_uploads()
    assert rows[0].attempts == 1
    assert rows[0].media_path == "/tmp/abc.mp4"

    repository.clear_pending("abc")
    assert repository.pending_uploads() == []


def test_record_pending_is_idempotent_and_keeps_media(tmp_path):
    from reddit2tube.database import VideoRepository

    repository = VideoRepository(tmp_path / "videos.sqlite3")
    repository.record_pending(
        "abc", "Title", "Description", "https://reddit.example/abc", "/tmp/a.mp4"
    )
    repository.record_pending("abc", "New title", "New description", "https://reddit.example/new")
    rows = repository.pending_uploads()
    assert len(rows) == 1
    assert rows[0].title == "New title"
    assert rows[0].source_url == "https://reddit.example/new"
    assert rows[0].media_path == "/tmp/a.mp4"
