"""Reddit integration kept behind a small boundary."""

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
