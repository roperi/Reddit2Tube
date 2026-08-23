def test_repository_initializes_and_is_idempotent(tmp_path):
    from reddit2tube.database import VideoRepository

    repository = VideoRepository(tmp_path / "nested" / "videos.sqlite3")
    repository.initialize()
    assert not repository.contains("abc")
    repository.mark_uploaded("abc", "A title", "youtube-id")
    repository.mark_uploaded("abc", "A title", "youtube-id")
    assert repository.contains("abc")
