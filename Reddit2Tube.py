"""
MIT License

Copyright (c) 2023 Roperi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv
from src.yt_downloader import download_video
from src.uploader import get_authenticated_service, initialize_upload
from src.database import mark_video_as_uploaded, is_video_uploaded
from src.reddit import authenticate_reddit, get_top_submissions
from utils import generate_updated_info, read_templates

# Load environment variables from the .env file
load_dotenv()


# Configure logging
# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Get paths
scriptdir = os.path.dirname(os.path.abspath(__file__))
mypath = os.path.join(scriptdir, 'log', 'Reddit2Tube.log')
# Create file handler which logs even DEBUG messages
fh = logging.FileHandler(mypath)
fh.setLevel(logging.DEBUG)
# Create console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('[%(levelname)s. %(name)s, (line #%(lineno)d) - %(asctime)s] %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add handlers to logger
logger.addHandler(fh)
logger.addHandler(ch)

# Get env variables
reddit_client_id = os.environ.get('REDDIT_CLIENT_ID')
reddit_client_secret = os.environ.get('REDDIT_CLIENT_SECRET')
reddit_user_agent = os.environ.get('REDDIT_USER_AGENT')
reddit_username = os.environ.get('REDDIT_USERNAME')
reddit_password = os.environ.get('REDDIT_PASSWORD')


def main(subreddit_name, reddit_num_submissions, time_filter, category, privacy_status, made_for_kids, just_download):
    try:
        # Authenticate with Reddit
        logger.info('Authenticating with Reddit')
        reddit_instance = authenticate_reddit(
            reddit_client_id,
            reddit_client_secret,
            reddit_user_agent,
            reddit_username,
            reddit_password
        )

        # Get the top n submissions
        top_videos = get_top_submissions(reddit_instance, subreddit_name, reddit_num_submissions, time_filter)

        # Example file paths for templates
        title_template_path = 'templates/title.txt'
        description_template_path = 'templates/description.txt'

        # Read templates from files
        title_template = read_templates(title_template_path)
        description_template = read_templates(description_template_path)

        for video in top_videos:
            # Download video
            video_url = 'https://www.reddit.com' + video.permalink
            video_title, video_description = generate_updated_info(video, title_template, description_template)

            # Check if the video is already uploaded
            uploaded = is_video_uploaded(video.id)

            if not uploaded:

                if 'v.redd.it' in video.url:

                    logger.info(f'Downloading `{video.title}` by {video.author.name} from `{video.url}`')
                    # Download the video
                    local_video_path = download_video(video_url, video_title)
                    logger.info(f'Downloaded video as `{local_video_path}`')
                    options = {'title': video_title,
                               'description': video_description,
                               'category': category,
                               'file': local_video_path,
                               }

                    if not just_download:
                        # Authenticate with YouTube
                        logger.info('Authenticating with Youtube')
                        youtube_instance = get_authenticated_service()

                        # Upload the video to YouTube
                        logging.info(f"Uploading '{video.title}' to Youtube.")
                        initialize_upload(youtube_instance, options, privacy_status, made_for_kids)
                        logging.info(f"Video '{video.title}' uploaded successfully")

                        # Mark the video as uploaded in the database
                        logging.info(f"Marking '{video.title}' as uploaded in database")
                        mark_video_as_uploaded(video.id, video.title)
                else:
                    logger.warning(f'No video found in the following url: {video.url} ')
            else:
                logger.warning(f"Video '{video.title}' was already uploaded")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download and upload top Reddit videos to YouTube.')

    parser.add_argument('--subreddit_name', type=str, help='Name of the subreddit')
    parser.add_argument('--reddit_num_submissions', default=2, type=int,
                        help='Number of Reddit submissions to process')
    parser.add_argument('--time_filter', type=str, default='day',
                        help='Time filter for Reddit submissions (e.g., "day", "week")')
    parser.add_argument('--category', type=str, default='22', help='YouTube video category')
    parser.add_argument('--privacy_status', type=str, default='private',
                        help='YouTube video privacy status (e.g., "private", "public", "unlisted")')
    parser.add_argument('--made_for_kids', action='store_true', help='Set if the video is made for kids')
    parser.add_argument('--just_download', action='store_true', help='Skip YouTube uploading')
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
    else:
        # Call the main function with provided command-line arguments
        main(
            args.subreddit_name, args.reddit_num_submissions, args.time_filter, args.category, args.privacy_status,
            args.made_for_kids, args.just_download
        )
