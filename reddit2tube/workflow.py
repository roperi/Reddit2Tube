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
from .models import RunOptions, RunSummary
from .reddit import authenticate_reddit, get_top_submissions
from .templates import read_template, render_templates
from .uploader import get_authenticated_service, initialize_upload


@dataclass(frozen=True)
class WorkflowDependencies:
    authenticate_reddit: Callable[..., Any] = authenticate_reddit
    get_top_submissions: Callable[..., Any] = get_top_submissions
    download_video: Callable[..., Path] = download_video
    get_authenticated_service: Callable[..., Any] = get_authenticated_service
    initialize_upload: Callable[..., str] = initialize_upload


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
            local_video = deps.download_video(
                video_url, video_title, download_dir=settings.download_dir
            )
            summary.downloaded += 1
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
                    options.privacy_status,
                    options.made_for_kids,
                )
                summary.uploaded += 1
            if not options.just_download:
                repo.mark_uploaded(submission_id, title, youtube_video_id)
        except Exception:
            summary.failures += 1
            log.exception("Failed to process submission %r", title)
    return summary
