"""Media inspection and validation for downloaded Reddit videos."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


class MediaValidationError(ValueError):
    """Raised when a downloaded media file cannot be safely uploaded."""


@dataclass(frozen=True)
class MediaInfo:
    path: Path
    duration: float
    width: int
    height: int
    video_codec: str
    audio_codec: str | None
    size: int

    @property
    def is_likely_short(self) -> bool:
        return self.width <= self.height and self.duration <= 180.0


def inspect_media(path: str | Path, *, decode: bool = False) -> MediaInfo:
    media_path = Path(path)
    if not media_path.is_file() or media_path.stat().st_size == 0:
        raise MediaValidationError(f"Media file is missing or empty: {media_path}")
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-show_entries",
                "stream=codec_type,codec_name,width,height",
                "-of",
                "json",
                str(media_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        probe = json.loads(result.stdout)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        raise MediaValidationError(f"ffprobe could not validate {media_path}: {error}") from error

    if decode:
        try:
            subprocess.run(
                ["ffmpeg", "-v", "error", "-i", str(media_path), "-map", "0", "-f", "null", "-"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            raise MediaValidationError(f"ffmpeg could not decode {media_path}: {error}") from error

    streams = probe.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    duration = float(probe.get("format", {}).get("duration") or 0)
    if not video or duration <= 0 or not video.get("width") or not video.get("height"):
        raise MediaValidationError(f"Media file has no usable video stream: {media_path}")
    return MediaInfo(
        path=media_path,
        duration=duration,
        width=int(video["width"]),
        height=int(video["height"]),
        video_codec=str(video.get("codec_name") or "unknown"),
        audio_codec=str(audio["codec_name"]) if audio else None,
        size=media_path.stat().st_size,
    )
