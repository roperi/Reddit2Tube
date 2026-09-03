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
