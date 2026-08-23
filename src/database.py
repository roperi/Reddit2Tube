"""Compatibility functions for the pre-package database API."""

from reddit2tube.config import load_settings
from reddit2tube.database import VideoRepository


def _repository() -> VideoRepository:
    return VideoRepository(load_settings().database_file)


def mark_video_as_uploaded(video_id, title):
    _repository().mark_uploaded(video_id, title)


def is_video_uploaded(video_id):
    return _repository().contains(video_id)
