"""YouTube OAuth and resumable upload integration."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from http import client
from typing import Any

import httplib2

from .config import Settings

logger = logging.getLogger("reddit2tube.youtube")
httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRY_STATUS_CODES = {500, 502, 503, 504}
RETRY_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    client.NotConnected,
    client.IncompleteRead,
    client.ImproperConnectionState,
    client.CannotSendRequest,
    client.CannotSendHeader,
    client.ResponseNotReady,
    client.BadStatusLine,
)


def get_authenticated_service(settings: Settings | None = None) -> Any:
    if settings is None:
        from .config import load_settings

        settings = load_settings()
        settings.validate()
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    if not settings.client_secrets_file:
        raise ValueError("A YouTube client secrets file is required.")
    token_file = settings.client_secrets_file.parent / "token.json"
    credentials = None
    if token_file.exists():
        try:
            credentials = Credentials.from_authorized_user_file(str(token_file), settings.scopes)
        except (OSError, ValueError) as error:
            logger.warning("Could not read saved YouTube token; re-authenticating: %s", error)
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(settings.client_secrets_file), list(settings.scopes)
        )
        credentials = flow.run_local_server(port=0)
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(credentials.to_json(), encoding="utf-8")
    return build(settings.api_service_name, settings.api_version, credentials=credentials)


def initialize_upload(
    youtube: Any,
    options: dict[str, Any],
    privacy_status: str,
    made_for_kids: bool,
    *,
    sleep: Callable[[float], None] = time.sleep,
    random_value: Callable[[], float] = random.random,
) -> str:
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    if privacy_status not in {"public", "private", "unlisted"}:
        raise ValueError(f"Unsupported privacy status: {privacy_status}")
    body = {
        "snippet": {
            "title": options["title"],
            "description": options["description"],
            "categoryId": options["category"],
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }
    if options.get("keywords"):
        body["snippet"]["tags"] = [
            tag.strip() for tag in options["keywords"].split(",") if tag.strip()
        ]
    media_body = MediaFileUpload(str(options["file"]), chunksize=1024 * 1024, resumable=True)
    request = youtube.videos().insert(part=",".join(body), body=body, media_body=media_body)
    response = None
    retry = 0
    while response is None:
        try:
            logger.info("Uploading %r in chunks (please wait)...", options["title"])
            _, response = request.next_chunk()
        except HttpError as error:
            if error.resp.status not in RETRY_STATUS_CODES:
                raise
            logger.warning("Retryable YouTube HTTP error %s", error.resp.status)
        except RETRY_EXCEPTIONS as error:
            logger.warning("Retryable YouTube transport error: %s", error)
        if response is None:
            retry += 1
            if retry > MAX_RETRIES:
                raise RuntimeError("YouTube upload exceeded the retry limit.")
            sleep(random_value() * (2**retry))
    video_id = response.get("id") if isinstance(response, dict) else None
    if not video_id:
        raise RuntimeError(f"YouTube returned an unexpected upload response: {response!r}")
    return str(video_id)
