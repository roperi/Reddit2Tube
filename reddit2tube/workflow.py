"""Application workflow coordinating integrations without owning their details."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Settings
from .database import VideoRepository
from .downloader import download_video
from .media import inspect_media
from .models import RunOptions, RunSummary
from .reddit import authenticate_reddit, get_top_submissions
from .templates import read_template, render_templates
from .uploader import UploadLimitReached, get_authenticated_service, initialize_upload


@dataclass(frozen=True)
class WorkflowDependencies:
    authenticate_reddit: Callable[..., Any] = authenticate_reddit
    get_top_submissions: Callable[..., Any] = get_top_submissions
    download_video: Callable[..., Path] = download_video
    get_authenticated_service: Callable[..., Any] = get_authenticated_service
    initialize_upload: Callable[..., str] = initialize_upload


def _download_env(settings: Settings) -> dict[str, str]:
    env: dict[str, str] = {}
    if settings.reddit_cookies_from_browser:
        env["REDDIT_COOKIES_FROM_BROWSER"] = settings.reddit_cookies_from_browser
    if settings.reddit_cookies_file:
        env["REDDIT_COOKIES_FILE"] = str(settings.reddit_cookies_file)
    return env


def run_workflow(
    settings: Settings,
    options: RunOptions,
    *,
    dependencies: WorkflowDependencies | None = None,
    repository: VideoRepository | None = None,
    logger: logging.Logger | None = None,
) -> RunSummary:
    deps = dependencies or WorkflowDependencies()
    log = logger or logging.getLogger("reddit2tube")
    settings.validate(require_youtube=not options.just_download)
    if options.reddit_num_submissions < 1:
        raise ValueError("reddit_num_submissions must be at least 1")
    if options.privacy_status not in {"public", "private", "unlisted"}:
        raise ValueError("privacy_status must be public, private, or unlisted")
    if options.troubleshooting_upload and options.just_download:
        raise ValueError("troubleshooting_upload requires YouTube upload mode")

    repo = repository or VideoRepository(settings.database_file)
    repo.initialize()
    title_template = read_template(settings.title_template_file)
    description_template = read_template(settings.description_template_file)
    reddit = deps.authenticate_reddit(
        settings.reddit_client_id,
        settings.reddit_client_secret,
        settings.reddit_user_agent,
        settings.reddit_username,
        settings.reddit_password,
    )
    submissions = deps.get_top_submissions(
        reddit, options.subreddit_name, options.reddit_num_submissions, options.time_filter
    )
    youtube = None
    download_env = _download_env(settings)
    summary = RunSummary()
    for submission in submissions:
        summary.examined += 1
        submission_id = str(getattr(submission, "id", ""))
        title = str(getattr(submission, "title", submission_id))
        url = str(getattr(submission, "url", ""))
        if repo.contains(submission_id):
            summary.skipped_uploaded += 1
            log.info("Skipping already processed video %r", title)
            continue
        if "v.redd.it" not in url:
            summary.skipped_non_video += 1
            log.warning("Skipping submission without a Reddit video URL: %s", url)
            continue
        try:
            permalink = str(getattr(submission, "permalink", ""))
            video_url = "https://www.reddit.com" + permalink if permalink.startswith("/") else url
            video_title, video_description = render_templates(
                submission, title_template, description_template
            )
            if not options.just_download:
                # Record intent before downloading so a crash or failure leaves a
                # durable record that can be retried without the Reddit listing.
                repo.record_pending(submission_id, video_title, video_description, video_url)
            local_video = deps.download_video(
                video_url, video_title, download_dir=settings.download_dir, env=download_env
            )
            summary.downloaded += 1
            if not options.just_download:
                repo.set_pending_media(submission_id, str(local_video))
            if options.troubleshooting_upload:
                media = inspect_media(local_video, decode=True)
                log.info(
                    "Validated media %s: %.1fs, %sx%s, %s/%s, %d bytes",
                    local_video,
                    media.duration,
                    media.width,
                    media.height,
                    media.video_codec,
                    media.audio_codec or "no-audio",
                    media.size,
                )
                if media.is_likely_short:
                    summary.skipped_non_video += 1
                    log.info("Skipping likely Short during troubleshooting: %r", title)
                    continue
                if not repo.reserve_upload_attempt(6):
                    log.warning("Troubleshooting upload limit reached; stopping this run")
                    break
            youtube_video_id = None
            if not options.just_download:
                if youtube is None:
                    log.info("Authenticating with YouTube")
                    youtube = deps.get_authenticated_service(settings)
                youtube_video_id = deps.initialize_upload(
                    youtube,
                    {
                        "title": video_title,
                        "description": video_description,
                        "category": options.category,
                        "file": local_video,
                    },
                    "private" if options.troubleshooting_upload else options.privacy_status,
                    options.made_for_kids,
                )
                summary.uploaded += 1
            if not options.just_download:
                repo.mark_uploaded(submission_id, title, youtube_video_id)
                repo.clear_pending(submission_id)
        except UploadLimitReached as error:
            summary.failures += 1
            if not options.just_download:
                repo.record_failure(submission_id, str(error))
            log.error("YouTube upload limit reached; stopping this run: %s", error)
            break
        except Exception as error:
            summary.failures += 1
            if not options.just_download:
                repo.record_failure(submission_id, str(error))
            log.exception("Failed to process submission %r", title)
    return summary


def retry_pending_uploads(
    settings: Settings,
    options: RunOptions,
    *,
    dependencies: WorkflowDependencies | None = None,
    repository: VideoRepository | None = None,
    logger: logging.Logger | None = None,
) -> RunSummary:
    """Re-upload submissions recorded as pending without consulting Reddit."""
    deps = dependencies or WorkflowDependencies()
    log = logger or logging.getLogger("reddit2tube")
    if options.just_download:
        raise ValueError("Retrying failed uploads requires YouTube upload mode")
    settings.validate(require_reddit=False, require_templates=False)
    repo = repository or VideoRepository(settings.database_file)
    repo.initialize()
    pending = repo.pending_uploads()
    summary = RunSummary()
    if not pending:
        log.info("No pending uploads to retry")
        return summary
    download_env = _download_env(settings)
    youtube = None
    for item in pending:
        summary.examined += 1
        submission_id = item.submission_id
        try:
            if repo.contains(submission_id):
                repo.clear_pending(submission_id)
                summary.skipped_uploaded += 1
                continue
            media_path = Path(item.media_path) if item.media_path else None
            if media_path is None or not media_path.is_file():
                if not item.source_url:
                    raise RuntimeError(f"No local media or source URL to retry {item.title!r}")
                log.info("Re-downloading %r for retry", item.title)
                media_path = deps.download_video(
                    item.source_url,
                    item.title,
                    download_dir=settings.download_dir,
                    env=download_env,
                )
                repo.set_pending_media(submission_id, str(media_path))
                summary.downloaded += 1
            if options.troubleshooting_upload and not repo.reserve_upload_attempt(6):
                log.warning("Troubleshooting upload limit reached; stopping retry")
                break
            if youtube is None:
                log.info("Authenticating with YouTube")
                youtube = deps.get_authenticated_service(settings)
            youtube_video_id = deps.initialize_upload(
                youtube,
                {
                    "title": item.title,
                    "description": item.description,
                    "category": options.category,
                    "file": media_path,
                },
                "private" if options.troubleshooting_upload else options.privacy_status,
                options.made_for_kids,
            )
            summary.uploaded += 1
            repo.mark_uploaded(submission_id, item.title, youtube_video_id)
            repo.clear_pending(submission_id)
        except UploadLimitReached as error:
            summary.failures += 1
            repo.record_failure(submission_id, str(error))
            log.error("YouTube upload limit reached; stopping retry: %s", error)
            break
        except Exception as error:
            summary.failures += 1
            repo.record_failure(submission_id, str(error))
            log.exception("Failed to retry submission %r", item.title)
    return summary
