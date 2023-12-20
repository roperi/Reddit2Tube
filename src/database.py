import os
import sqlite3
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

database_file = os.environ.get('DATABASE_FILE')


def mark_video_as_uploaded(video_id, title):
    # Function to mark a video as uploaded in the database
    with sqlite3.connect(database_file) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO uploaded_videos (video_id, title, upload_datetime)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(video_id) DO NOTHING
        ''', (video_id, title))
        conn.commit()


def is_video_uploaded(video_id):
    # Function to check if a video is already uploaded
    with sqlite3.connect(database_file) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT EXISTS(SELECT 1 FROM uploaded_videos WHERE video_id = ?) AS uploaded
        ''', (video_id,))
        result = cursor.fetchone()
        if result:
            return bool(result[0])
        else:
            return False
