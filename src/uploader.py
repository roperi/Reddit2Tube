import os
import random
import time
from http import client
import httplib2
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

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
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    if run_env == 'development':
        credentials = flow.run_local_server()
    else:
        credentials = flow.run_console()
    return build(api_service_name, api_version, credentials=credentials)


def initialize_upload(youtube, options, privacy_status):
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
            'selfDeclaredMadeForKids': False,
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
    resumable_upload(insert_request)


def resumable_upload(request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print('Uploading file...')
            status, response = request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print(f'Video id {response.get("id")} was successfully uploaded')
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
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit('No longer attempting to retry.')
            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print(f'Sleeping {sleep_seconds} seconds and then retrying...')
            time.sleep(sleep_seconds)