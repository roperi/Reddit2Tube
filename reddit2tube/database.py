"""SQLite persistence for idempotent uploads."""

import sqlite3
from pathlib import Path


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
