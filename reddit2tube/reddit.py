"""Reddit integration kept behind a small boundary."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


def authenticate_reddit(
    reddit_client_id: str,
    reddit_client_secret: str,
    reddit_user_agent: str,
    reddit_username: str,
    reddit_password: str,
) -> Any:
    import praw

    return praw.Reddit(
        client_id=reddit_client_id,
        client_secret=reddit_client_secret,
        user_agent=reddit_user_agent,
        username=reddit_username,
        password=reddit_password,
    )


def get_top_submissions(
    reddit: Any, subreddit_name: str, num_submissions: int, time_filter: str
) -> Any:
    return reddit.subreddit(subreddit_name).top(time_filter=time_filter, limit=num_submissions)


def _reddit_video(submission: Any) -> Mapping[str, Any] | None:
    def from_media(media: Any) -> Mapping[str, Any] | None:
        if isinstance(media, Mapping):
            video = media.get("reddit_video")
            if isinstance(video, Mapping):
                return video
        return None

    for attribute in ("secure_media", "media"):
        video = from_media(getattr(submission, attribute, None))
        if video is not None:
            return video
    for parent in getattr(submission, "crosspost_parent_list", None) or ():
        if isinstance(parent, Mapping):
            for attribute in ("secure_media", "media"):
                video = from_media(parent.get(attribute))
                if video is not None:
                    return video
    return None


def get_reddit_video_url(submission: Any) -> str | None:
    """Return a direct v.redd.it media URL for a submission.

    yt-dlp's Reddit extractor fetches ``reddit.com/.../.json``, which some
    networks cannot reach even with a logged-in browser session. PRAW already
    retrieved the submission through the OAuth API, so its Reddit-hosted media
    URL can be downloaded directly. HLS is preferred because it includes an
    audio track; the MP4 fallback is video-only.
    """
    video = _reddit_video(submission)
    if video is not None:
        for key in ("hls_url", "dash_url", "fallback_url"):
            value = video.get(key)
            if value:
                return str(value)
    url = str(getattr(submission, "url", ""))
    match = re.match(r"https?://v\.redd\.it/([^/?#]+)", url)
    if match:
        return f"https://v.redd.it/{match.group(1)}/HLSPlaylist.m3u8"
    return None
