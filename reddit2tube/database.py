"""SQLite persistence for idempotent uploads."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import PendingUpload


class VideoRepository:
    def __init__(self, database_file: str | Path):
        self.database_file = Path(database_file)

    def initialize(self) -> None:
        self.database_file.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_file) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS uploaded_videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    youtube_video_id TEXT,
                    upload_datetime DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._add_column_if_missing(connection, "youtube_video_id", "TEXT")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS upload_attempts (
                    attempt_date TEXT PRIMARY KEY,
                    attempts INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_uploads (
                    submission_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    source_url TEXT NOT NULL DEFAULT '',
                    media_path TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    created_datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_datetime DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    @staticmethod
    def _add_column_if_missing(connection: sqlite3.Connection, name: str, definition: str) -> None:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(uploaded_videos)")}
        if name not in columns:
            connection.execute(f"ALTER TABLE uploaded_videos ADD COLUMN {name} {definition}")

    def contains(self, video_id: str) -> bool:
        self.initialize()
        with sqlite3.connect(self.database_file) as connection:
            row = connection.execute(
                "SELECT 1 FROM uploaded_videos WHERE video_id = ?", (video_id,)
            ).fetchone()
        return row is not None

    def mark_uploaded(self, video_id: str, title: str, youtube_video_id: str | None = None) -> None:
        self.initialize()
        with sqlite3.connect(self.database_file) as connection:
            connection.execute(
                """
                INSERT INTO uploaded_videos (video_id, title, youtube_video_id)
                VALUES (?, ?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    title = excluded.title,
                    youtube_video_id = COALESCE(
                        excluded.youtube_video_id, uploaded_videos.youtube_video_id
                    )
                """,
                (video_id, title, youtube_video_id),
            )

    def reserve_upload_attempt(self, limit: int, *, now: datetime | None = None) -> bool:
        """Atomically reserve an upload attempt for the current UTC day."""
        if limit < 1:
            raise ValueError("Upload attempt limit must be positive.")
        self.initialize()
        attempt_date = (now or datetime.now(timezone.utc)).date().isoformat()
        with sqlite3.connect(self.database_file, isolation_level="IMMEDIATE") as connection:
            current = connection.execute(
                "SELECT attempts FROM upload_attempts WHERE attempt_date = ?", (attempt_date,)
            ).fetchone()
            attempts = int(current[0]) if current else 0
            if attempts >= limit:
                return False
            connection.execute(
                """
                INSERT INTO upload_attempts (attempt_date, attempts) VALUES (?, 1)
                ON CONFLICT(attempt_date) DO UPDATE SET attempts = attempts + 1
                """,
                (attempt_date,),
            )
            return True

    def record_pending(
        self,
        submission_id: str,
        title: str,
        description: str,
        source_url: str,
        media_path: str | None = None,
    ) -> None:
        """Register a submission intended for upload so it can be retried later."""
        self.initialize()
        with sqlite3.connect(self.database_file) as connection:
            connection.execute(
                """
                INSERT INTO pending_uploads
                    (submission_id, title, description, source_url, media_path)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(submission_id) DO UPDATE SET
                    title = excluded.title,
                    description = excluded.description,
                    source_url = excluded.source_url,
                    media_path = COALESCE(excluded.media_path, pending_uploads.media_path),
                    updated_datetime = CURRENT_TIMESTAMP
                """,
                (submission_id, title, description, source_url, media_path),
            )

    def set_pending_media(self, submission_id: str, media_path: str) -> None:
        """Associate a downloaded media file with a pending upload."""
        self.initialize()
        with sqlite3.connect(self.database_file) as connection:
            connection.execute(
                """
                UPDATE pending_uploads
                SET media_path = ?, updated_datetime = CURRENT_TIMESTAMP
                WHERE submission_id = ?
                """,
                (media_path, submission_id),
            )

    def record_failure(self, submission_id: str, error: str) -> None:
        """Record a failed attempt against a pending upload, if it is tracked."""
        self.initialize()
        with sqlite3.connect(self.database_file) as connection:
            connection.execute(
                """
                UPDATE pending_uploads
                SET attempts = attempts + 1,
                    last_error = ?,
                    updated_datetime = CURRENT_TIMESTAMP
                WHERE submission_id = ?
                """,
                (error, submission_id),
            )

    def pending_uploads(self) -> list[PendingUpload]:
        """Return tracked uploads that have not succeeded yet."""
        self.initialize()
        with sqlite3.connect(self.database_file) as connection:
            rows = connection.execute(
                """
                SELECT submission_id, title, description, source_url, media_path,
                       attempts, last_error
                FROM pending_uploads
                ORDER BY created_datetime, submission_id
                """
            ).fetchall()
        return [
            PendingUpload(
                submission_id=row[0],
                title=row[1],
                description=row[2],
                source_url=row[3],
                media_path=row[4],
                attempts=row[5],
                last_error=row[6],
            )
            for row in rows
        ]

    def clear_pending(self, submission_id: str) -> None:
        """Remove a pending upload after it succeeds."""
        self.initialize()
        with sqlite3.connect(self.database_file) as connection:
            connection.execute(
                "DELETE FROM pending_uploads WHERE submission_id = ?", (submission_id,)
            )
