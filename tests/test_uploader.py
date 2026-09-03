import pytest

from reddit2tube.uploader import UploadLimitReached, initialize_upload


class FakeUploadRequest:
    def __init__(self, responses):
        self.responses = iter(responses)

    def next_chunk(self):
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


class FakeVideos:
    def __init__(self, request):
        self.request = request

    def insert(self, **kwargs):
        return self.request


class FakeYouTube:
    def __init__(self, request):
        self._videos = FakeVideos(request)

    def videos(self):
        return self._videos


def test_initialize_upload_recovers_after_transport_error(monkeypatch, tmp_path):
    pytest.importorskip("googleapiclient.http")

    class Status:
        def progress(self):
            return 1.0

    import googleapiclient.http

    monkeypatch.setattr(
        googleapiclient.http,
        "MediaFileUpload",
        lambda *args, **kwargs: object(),
    )
    request = FakeUploadRequest([OSError("connection closed"), (Status(), {"id": "abc"})])
    youtube = FakeYouTube(request)
    assert (
        initialize_upload(
            youtube,
            {
                "title": "Title",
                "description": "Description",
                "category": "22",
                "file": tmp_path / "v.mp4",
            },
            "private",
            False,
            sleep=lambda _: None,
            random_value=lambda: 0,
            max_retries=1,
        )
        == "abc"
    )


def test_initialize_upload_raises_specific_limit_error(monkeypatch, tmp_path):
    pytest.importorskip("googleapiclient.errors")

    from googleapiclient.errors import ResumableUploadError

    class Response:
        status = 400
        reason = "Bad Request"

    monkeypatch.setattr(
        "googleapiclient.http.MediaFileUpload",
        lambda *args, **kwargs: object(),
    )
    error = ResumableUploadError(
        Response(),
        b'{"error":{"message":"The user has exceeded the number of videos they may upload."}}',
    )
    with pytest.raises(UploadLimitReached):
        initialize_upload(
            FakeYouTube(FakeUploadRequest([error])),
            {
                "title": "Title",
                "description": "Description",
                "category": "22",
                "file": tmp_path / "v.mp4",
            },
            "private",
            False,
        )
