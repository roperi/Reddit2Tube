"""Small domain models shared by the application layers."""

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
