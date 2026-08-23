"""Application configuration and validation."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(ValueError):
    """Raised when the application cannot start with supplied settings."""


def _path(value: str | None, base_dir: Path, default: str) -> Path:
    selected = value or default
    result = Path(selected).expanduser()
    return result if result.is_absolute() else base_dir / result


@dataclass(frozen=True)
class Settings:
    database_file: Path
    title_template_file: Path
    description_template_file: Path
    download_dir: Path
    reddit_client_id: str | None
    reddit_client_secret: str | None
    reddit_user_agent: str | None
    reddit_username: str | None
    reddit_password: str | None
    reddit_cookies_from_browser: str | None
    reddit_cookies_file: Path | None
    client_secrets_file: Path | None
    scopes: tuple[str, ...]
    api_service_name: str
    api_version: str

    def validate(self, *, require_youtube: bool = True) -> None:
        required = {
            "REDDIT_CLIENT_ID": self.reddit_client_id,
            "REDDIT_CLIENT_SECRET": self.reddit_client_secret,
            "REDDIT_USER_AGENT": self.reddit_user_agent,
            "REDDIT_USERNAME": self.reddit_username,
            "REDDIT_PASSWORD": self.reddit_password,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ConfigurationError("Missing required Reddit configuration: " + ", ".join(missing))
        if self.reddit_cookies_from_browser and self.reddit_cookies_file:
            raise ConfigurationError(
                "Set only one of REDDIT_COOKIES_FROM_BROWSER or REDDIT_COOKIES_FILE."
            )
        if self.reddit_cookies_file and not self.reddit_cookies_file.is_file():
            raise ConfigurationError(
                f"Reddit cookie file does not exist: {self.reddit_cookies_file}"
            )
        if not self.title_template_file.is_file():
            raise ConfigurationError(f"Title template does not exist: {self.title_template_file}")
        if not self.description_template_file.is_file():
            raise ConfigurationError(
                f"Description template does not exist: {self.description_template_file}"
            )
        if require_youtube:
            if not self.client_secrets_file:
                raise ConfigurationError("CLIENT_SECRETS_FILE is required when uploading.")
            if not self.client_secrets_file.is_file():
                raise ConfigurationError(
                    f"YouTube client secrets file does not exist: {self.client_secrets_file}"
                )
            if not self.scopes:
                raise ConfigurationError("At least one YouTube OAuth scope is required.")


def load_settings(
    env: Mapping[str, str] | None = None,
    *,
    base_dir: Path | None = None,
    load_dotenv_file: bool = True,
) -> Settings:
    """Load settings without validating service-specific requirements."""
    if env is None:
        if load_dotenv_file:
            try:
                from dotenv import load_dotenv

                load_dotenv()
            except ImportError:
                pass
        env = os.environ
    root = (base_dir or Path.cwd()).resolve()
    cookie_file = env.get("REDDIT_COOKIES_FILE")
    client_secrets = env.get("CLIENT_SECRETS_FILE")
    scopes = tuple(scope.strip() for scope in env.get("SCOPES", "").split(",") if scope.strip())
    return Settings(
        database_file=_path(env.get("DATABASE_FILE"), root, "db.sqlite3"),
        title_template_file=_path(env.get("TITLE_TEMPLATE_FILE"), root, "templates/title.txt"),
        description_template_file=_path(
            env.get("DESCRIPTION_TEMPLATE_FILE"), root, "templates/description.txt"
        ),
        download_dir=_path(env.get("DOWNLOAD_DIR"), root, "/tmp/reddit2tube"),
        reddit_client_id=env.get("REDDIT_CLIENT_ID"),
        reddit_client_secret=env.get("REDDIT_CLIENT_SECRET"),
        reddit_user_agent=env.get("REDDIT_USER_AGENT"),
        reddit_username=env.get("REDDIT_USERNAME"),
        reddit_password=env.get("REDDIT_PASSWORD"),
        reddit_cookies_from_browser=env.get("REDDIT_COOKIES_FROM_BROWSER"),
        reddit_cookies_file=_path(cookie_file, root, "") if cookie_file else None,
        client_secrets_file=_path(client_secrets, root, "") if client_secrets else None,
        scopes=scopes,
        api_service_name=env.get("API_SERVICE_NAME", "youtube"),
        api_version=env.get("API_VERSION", "v3"),
    )
