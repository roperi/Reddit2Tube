from types import SimpleNamespace

import pytest

from reddit2tube.config import Settings


@pytest.fixture
def submission():
    return SimpleNamespace(
        id="abc123",
        title="A good cat video",
        permalink="/r/cats/comments/abc123/a_good_cat_video/",
        url="https://v.redd.it/example",
        author=SimpleNamespace(name="roperi"),
        selftext="",
        score=42,
        num_comments=3,
        created_utc=123.0,
        subreddit=SimpleNamespace(display_name="cats"),
        is_self=False,
        link_flair_text=None,
        locked=False,
    )


@pytest.fixture
def settings(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "title.txt").write_text("{title} by {author}", encoding="utf-8")
    (templates / "description.txt").write_text("r/{subreddit}", encoding="utf-8")
    client_secrets = tmp_path / "config" / "client_secret.json"
    client_secrets.parent.mkdir()
    client_secrets.write_text("{}", encoding="utf-8")
    return Settings(
        database_file=tmp_path / "data" / "videos.sqlite3",
        title_template_file=templates / "title.txt",
        description_template_file=templates / "description.txt",
        download_dir=tmp_path / "downloads",
        reddit_client_id="id",
        reddit_client_secret="secret",
        reddit_user_agent="agent",
        reddit_username="user",
        reddit_password="password",
        reddit_cookies_from_browser=None,
        reddit_cookies_file=None,
        client_secrets_file=client_secrets,
        scopes=("scope",),
        api_service_name="youtube",
        api_version="v3",
    )
