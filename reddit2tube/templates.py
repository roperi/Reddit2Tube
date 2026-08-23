"""Template loading and Reddit submission rendering."""

from pathlib import Path
from typing import Any


def read_template(file_path: str | Path) -> str:
    return Path(file_path).read_text(encoding="utf-8").strip()


def _author_name(submission: Any) -> str:
    author = getattr(submission, "author", None)
    return getattr(author, "name", "[deleted]") if author else "[deleted]"


def submission_context(submission: Any) -> dict[str, Any]:
    title = str(getattr(submission, "title", ""))
    display_title = title if len(title) <= 70 else title[:67] + "..."
    return {
        "title": display_title,
        "id": getattr(submission, "id", ""),
        "author": _author_name(submission),
        "selftext": getattr(submission, "selftext", ""),
        "url": getattr(submission, "url", ""),
        "score": getattr(submission, "score", 0),
        "num_comments": getattr(submission, "num_comments", 0),
        "created_utc": getattr(submission, "created_utc", ""),
        "subreddit": str(getattr(submission, "subreddit", "")),
        "is_self": getattr(submission, "is_self", False),
        "link_flair_text": getattr(submission, "link_flair_text", "") or "",
        "locked": getattr(submission, "locked", False),
    }


def render_templates(
    submission: Any, title_template: str, description_template: str
) -> tuple[str, str]:
    context = submission_context(submission)
    return title_template.format(**context), description_template.format(**context)
