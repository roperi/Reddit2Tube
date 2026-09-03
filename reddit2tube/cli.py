"""Command-line interface for Reddit2Tube."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .config import ConfigurationError, load_settings
from .logging_config import configure_logging
from .models import RunOptions
from .workflow import run_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download and upload top Reddit videos to YouTube."
    )
    parser.add_argument("--subreddit_name", help="Name of the subreddit")
    parser.add_argument("--reddit_num_submissions", default=2, type=int, help="Number to process")
    parser.add_argument(
        "--time_filter", default="day", help='Reddit time filter, e.g. "day" or "week"'
    )
    parser.add_argument("--category", default="22", help="YouTube video category")
    parser.add_argument(
        "--privacy_status", choices=["public", "private", "unlisted"], default="private"
    )
    parser.add_argument("--made_for_kids", action="store_true", help="Declare videos made for kids")
    parser.add_argument("--just_download", action="store_true", help="Skip YouTube uploading")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--troubleshooting-upload",
        action="store_true",
        help="Use private, long-form-only uploads with a six-attempt daily cap",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.subreddit_name:
        parser.print_help()
        return 0
    logger = configure_logging(Path.cwd() / "log" / "Reddit2Tube.log", verbose=args.verbose)
    options = RunOptions(
        subreddit_name=args.subreddit_name,
        reddit_num_submissions=args.reddit_num_submissions,
        time_filter=args.time_filter,
        category=args.category,
        privacy_status=args.privacy_status,
        made_for_kids=args.made_for_kids,
        just_download=args.just_download,
        troubleshooting_upload=args.troubleshooting_upload,
    )
    try:
        summary = run_workflow(load_settings(), options, logger=logger)
    except (ConfigurationError, ValueError, OSError) as error:
        logger.error("Cannot start Reddit2Tube: %s", error)
        return 2
    except Exception as error:
        logger.exception("Reddit2Tube failed unexpectedly: %s", error)
        return 1
    logger.info(
        "Run complete: examined=%d skipped=%d downloaded=%d uploaded=%d failures=%d",
        summary.examined,
        summary.skipped_non_video + summary.skipped_uploaded,
        summary.downloaded,
        summary.uploaded,
        summary.failures,
    )
    return 1 if not summary.successful else 0
