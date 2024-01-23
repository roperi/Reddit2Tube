#!/usr/bin/env python3
import os
import sys
import random
import time
import logging
from http import client
import httplib2
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

from dotenv import load_dotenv

# Configure logging
# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Get the root directory of the project
scriptdir = os.path.dirname(os.path.abspath(__file__))
rootdir = os.path.dirname(scriptdir)
mypath = os.path.join(rootdir, 'log', 'Reddit2Tube.log')
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

# Load environment variables from the .env file
load_dotenv()

# Get env variables
client_secrets_file = os.environ.get('CLIENT_SECRETS_FILE')
scopes = [os.environ.get('SCOPES')]
api_service_name = os.environ.get('API_SERVICE_NAME')
api_version = os.environ.get('API_VERSION')
run_env = os.environ.get('RUN_ENV')


# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRY_EXCEPTIONS = (
    httplib2.HttpLib2Error, IOError, client.NotConnected,
    client.IncompleteRead, client.ImproperConnectionState,
    client.CannotSendRequest, client.CannotSendHeader,
    client.ResponseNotReady, client.BadStatusLine
)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRY_STATUS_CODES = [500, 502, 503, 504]


# Authorize the request and store authorization credentials.
def get_authenticated_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("config/token.json"):
        try:
            creds = Credentials.from_authorized_user_file("config/token.json", scopes)
            creds.refresh(Request())
        except Exception as error:
            # if refresh token fails, reset creds to none.
            creds = None
            logger.warning(f'Refresh token expired requesting authorization again: {error}')
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("config/token.json", "w") as token:
            token.write(creds.to_json())

    return build(api_service_name, api_version, credentials=creds)


def initialize_upload(youtube, options, privacy_status, made_for_kids):
    # Extract keywords from the options
    tags = None
    if options.get('keywords'):
        tags = options.get('keywords').split(',')
    # Build the request body
    body = {
        'snippet': {
            'title': options.get('title'),
            'description': options.get('description'),
            'tags': tags,
            'categoryId': options.get('category'),
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': made_for_kids,
        },
    }
    # Create a MediaFileUpload object for the video file
    media_body = MediaFileUpload(options.get('file'), chunksize=1024*1024, resumable=True)
    # Call the API videos.insert method to create and upload the video
    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media_body
    )
    # Perform the resumable upload
    resumable_upload(insert_request, options.get('title'))


def resumable_upload(request, video_title):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            logger.info(f'Uploading `{video_title}` in chunks (please wait)...')
            status, response = request.next_chunk()
            if response is not None:
                if 'id' in response:
                    logger.info(f'Video id {response.get("id")} was successfully uploaded')
                else:
                    exit(f'The upload failed with an unexpected response: {response}')
        except HttpError as e:
            if e.resp.status in RETRY_STATUS_CODES:
                error = f'A HTTP error {e.resp.status} occurred:\ne.content'
            else:
                raise
        except RETRY_EXCEPTIONS as e:
            error = f'A error occurred: {e}'
        if error is not None:
            logger.error(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit('No longer attempting to retry.')
            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            logger.info(f'Sleeping {sleep_seconds} seconds and then retrying...')
            time.sleep(sleep_seconds)


def parse_args():
    parser = argparse.ArgumentParser(description='YouTube Video Uploader')
    parser.add_argument('--title', required=True, help='Title of the video')
    parser.add_argument('--description', required=True, help='Description of the video')
    parser.add_argument('--keywords', help='Keywords for the video (comma-separated)')
    parser.add_argument('--category', default='22', help='Category ID for the video')
    parser.add_argument('--file', required=True, help='Path to the video file')
    parser.add_argument('--privacy', choices=['public', 'private', 'unlisted'], default='private',
                        help='Privacy status of the video (public, private, or unlisted)')
    parser.add_argument('--made_for_kids', action='store_true', help='Set if the video is made for kids')

    return parser.parse_args()


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()

    # Define video upload options based on command line arguments
    arg_options = {
        'title': args.title,
        'description': args.description,
        'keywords': args.keywords,
        'category': args.category,
        'file': args.file,
    }

    # Get authenticated YouTube service
    youtube_service = get_authenticated_service()

    # Initialize and perform video upload
    initialize_upload(youtube_service, arg_options, args.privacy, args.made_for_kids)
