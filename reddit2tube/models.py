"""Small domain models shared by the application layers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunOptions:
    subreddit_name: str
    reddit_num_submissions: int = 2
    time_filter: str = "day"
    category: str = "22"
    privacy_status: str = "private"
    made_for_kids: bool = False
    just_download: bool = False
    troubleshooting_upload: bool = False


@dataclass(frozen=True)
class PendingUpload:
    """A submission intended for upload that has not yet succeeded."""

    submission_id: str
    title: str
    description: str
    source_url: str
    media_path: str | None
    attempts: int
    last_error: str | None


@dataclass
class RunSummary:
    examined: int = 0
    skipped_non_video: int = 0
    skipped_uploaded: int = 0
    downloaded: int = 0
    uploaded: int = 0
    failures: int = 0

    @property
    def successful(self) -> bool:
        return self.failures == 0

    def merge(self, other: RunSummary) -> RunSummary:
        return RunSummary(
            examined=self.examined + other.examined,
            skipped_non_video=self.skipped_non_video + other.skipped_non_video,
            skipped_uploaded=self.skipped_uploaded + other.skipped_uploaded,
            downloaded=self.downloaded + other.downloaded,
            uploaded=self.uploaded + other.uploaded,
            failures=self.failures + other.failures,
        )
