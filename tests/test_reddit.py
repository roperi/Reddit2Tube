from types import SimpleNamespace

from reddit2tube.reddit import get_reddit_video_url


def test_prefers_signed_hls_media_url():
    submission = SimpleNamespace(
        url="https://v.redd.it/example",
        secure_media=None,
        media={
            "reddit_video": {
                "hls_url": "https://v.redd.it/example/HLSPlaylist.m3u8?a=token",
                "fallback_url": "https://v.redd.it/example/CMAF_720.mp4?source=fallback",
            }
        },
    )
    assert get_reddit_video_url(submission) == "https://v.redd.it/example/HLSPlaylist.m3u8?a=token"


def test_uses_media_from_crosspost_parent():
    submission = SimpleNamespace(
        url="https://v.redd.it/crosspost",
        secure_media=None,
        media=None,
        crosspost_parent_list=[
            {
                "media": {
                    "reddit_video": {
                        "hls_url": "https://v.redd.it/original/HLSPlaylist.m3u8?a=token"
                    }
                }
            }
        ],
    )
    assert get_reddit_video_url(submission) == "https://v.redd.it/original/HLSPlaylist.m3u8?a=token"


def test_secure_media_is_checked_before_media():
    submission = SimpleNamespace(
        url="https://v.redd.it/example",
        secure_media={"reddit_video": {"hls_url": "https://v.redd.it/example/secure.m3u8"}},
        media={"reddit_video": {"hls_url": "https://v.redd.it/example/plain.m3u8"}},
    )
    assert get_reddit_video_url(submission) == "https://v.redd.it/example/secure.m3u8"


def test_derives_plain_hls_url_when_media_is_missing():
    submission = SimpleNamespace(url="https://v.redd.it/example")
    assert get_reddit_video_url(submission) == "https://v.redd.it/example/HLSPlaylist.m3u8"


def test_returns_none_for_external_media():
    submission = SimpleNamespace(url="https://www.youtube.com/watch?v=abc123", media=None)
    assert get_reddit_video_url(submission) is None
