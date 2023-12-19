import yt_dlp


def download_video(video_url):
    """Download a video from the given URL and return video path."""

    download_options = {
        'outtmpl': '/tmp/%(title)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(download_options) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        video_path = ydl.prepare_filename(info_dict)

    return video_path
