import pytest

from reddit2tube.config import ConfigurationError, load_settings


def test_load_settings_resolves_relative_paths(tmp_path):
    settings = load_settings(
        {
            "DATABASE_FILE": "data.sqlite3",
            "DOWNLOAD_DIR": "downloads",
            "SCOPES": "one, two",
        },
        base_dir=tmp_path,
        load_dotenv_file=False,
    )
    assert settings.database_file == (tmp_path / "data.sqlite3").resolve()
    assert settings.download_dir == (tmp_path / "downloads").resolve()
    assert settings.scopes == ("one", "two")


def test_validate_reports_missing_reddit_configuration(settings):
    missing = settings.__class__(**{**settings.__dict__, "reddit_password": None})
    with pytest.raises(ConfigurationError, match="REDDIT_PASSWORD"):
        missing.validate(require_youtube=False)


def test_validate_requires_youtube_files(settings, tmp_path):
    missing = settings.__class__(**{**settings.__dict__, "client_secrets_file": None, "scopes": ()})
    with pytest.raises(ConfigurationError, match="CLIENT_SECRETS_FILE"):
        missing.validate()
    secrets = tmp_path / "client_secret.json"
    secrets.write_text("{}", encoding="utf-8")
    configured = settings.__class__(
        **{
            **settings.__dict__,
            "client_secrets_file": secrets,
            "scopes": ("scope",),
        }
    )
    configured.validate()


def test_validate_can_skip_reddit_and_templates_for_retry(settings):
    reduced = settings.__class__(
        **{
            **settings.__dict__,
            "reddit_client_id": None,
            "reddit_client_secret": None,
            "reddit_user_agent": None,
            "reddit_username": None,
            "reddit_password": None,
            "title_template_file": settings.title_template_file.parent / "missing-title.txt",
            "description_template_file": settings.description_template_file.parent
            / "missing-description.txt",
        }
    )
    reduced.validate(require_reddit=False, require_templates=False)
    with pytest.raises(ConfigurationError, match="REDDIT_CLIENT_ID"):
        reduced.validate(require_reddit=True)
