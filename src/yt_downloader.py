"""Compatibility imports for the pre-package module path."""

from reddit2tube.downloader import (
    download_video,
    get_download_options,
    is_reddit_metadata_error,
    safe_filename,
)

__all__ = ["download_video", "get_download_options", "is_reddit_metadata_error", "safe_filename"]
