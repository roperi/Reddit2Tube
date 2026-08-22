import os

import yt_dlp


def _get_download_options():
    """Build yt-dlp options, including optional Reddit browser cookies."""
    cookies_from_browser = os.environ.get('REDDIT_COOKIES_FROM_BROWSER')
    cookies_file = os.environ.get('REDDIT_COOKIES_FILE')

    if cookies_from_browser and cookies_file:
        raise ValueError(
            'Set only one of REDDIT_COOKIES_FROM_BROWSER or REDDIT_COOKIES_FILE.'
        )

    download_options = {
        'outtmpl': '/tmp/%(title)s.%(ext)s',
    }

    if cookies_from_browser:
        # yt-dlp accepts (browser, profile, keyring, container). Keeping the
        # browser value in the environment means cookie contents never enter
        # the application configuration or logs.
        browser_parts = cookies_from_browser.split(':', 1)
        download_options['cookiesfrombrowser'] = tuple(browser_parts)
    elif cookies_file:
        if not os.path.isfile(os.path.expanduser(cookies_file)):
            raise FileNotFoundError(f'Reddit cookie file does not exist: {cookies_file}')
        download_options['cookiefile'] = os.path.expanduser(cookies_file)

    return download_options


def _is_reddit_metadata_error(error):
    message = str(error).lower()
    return any(
        marker in message
        for marker in (
            'failed to parse json',
            'unable to download json metadata',
            'account authentication is required',
        )
    )


def download_video(video_url, video_title):
    """Download a video from the given URL and return video path."""

    download_options = _get_download_options()
    download_options['outtmpl'] = f'/tmp/{video_title}.%(ext)s'

    try:
        with yt_dlp.YoutubeDL(download_options) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            video_path = ydl.prepare_filename(info_dict)
    except yt_dlp.utils.DownloadError as error:
        if _is_reddit_metadata_error(error):
            raise RuntimeError(
                'Reddit blocked the metadata request or returned an anti-bot '
                'challenge. Upgrade yt-dlp and, if the error persists, set '
                'REDDIT_COOKIES_FROM_BROWSER (for example, firefox) or '
                'REDDIT_COOKIES_FILE to cookies from a browser session that '
                'can open the post.'
            ) from error
        raise

    return video_path
