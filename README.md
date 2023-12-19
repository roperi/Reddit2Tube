<h1 align="center">Reddit2Tube</h1>
<h2 align="center">Download and Upload Top Reddit Videos to Youtube</h2>

---

## Main libraries used 
- Praw
- yt_dlp
- google-auth et al
- google-api-python-client

### Requirements

- Python +3.8
- Access to YouTube Data API v3
- Reddit app

## Getting your Reddit app credentials

These instructions assume you have a Reddit account.  

1. Go to > https://www.reddit.com/prefs/apps/
2. Fill form:
   * Name - your app name (e.g. "Cool app")
   * Description - what your app does (e.g. "My Cool app gets my favourite videos")
   * Select "script"
3. Click on Create app
4. Copy your client ID and secret key in a safe place

## Getting access to YouTube API v3
If possible, check a guide elsewhere on the details of how to do this. 

In general this is how it is done:

1. Go to Google Cloud Console > https://console.cloud.google.com/
2. In `Enabled APIs and services`: 
   - Add YouTube Data API v3
   - Add scope: `https://www.googleapis.com/auth/youtube.upload`
4. In `Credentials`:
   - Create an API Key 
   - Create OAuth 2.O client ID  to get client ID and its secret. 
     - Download the credentials as `client_secret.json` and put it in `config` folder
     - Use **Desktop client** to authenticate in your browser.
4. In `OAuth consent screen`:
   - Add Test user
   - Select 'External' in User type 

**Important**
* You will have a quota limit of 10,000 queries a day (this is equivalent to uploading no more than 6 videos at a cost of 1600 queries per video)
* YouTube will put all your uploaded videos in "Private view / marked as spam" even if you publish them in Public mode. This is to done to apps it doesn't trust yet. Therefore... 
* You'll have to ask for an app audit and verify your app to publish them in public mode, and/or increase your quota limits.


### Install

Create virtual environment
```
virtualenv -p python3 ~/.virtualenvs/Reddit2Tube
```

Active it
```
source ~/.virtualenvs/Reddit2Tube/bin/activate
```

Git clone 

```
git clone https://github.com/roperi/Reddit2Tube.git
```

Install dependencies
```
cd Reddit2Tube/
pip install - requirements.txt
```

### Configure
Create .env file in root folder

```commandline
touch .env
```
Add the following to .env file:
```
# .env

# Reddit
REDDIT_CLIENT_ID="YOUR-REDDIT-CLIENT-ID"
REDDIT_CLIENT_SECRET="YOUR-REDDIT-SECRET"
REDDIT_USERNAME="YOUR-REDDIT_USERNAME"
REDDIT_PASSWORD="YOUR-REDDIT_PASSWORD"
REDDIT_USER_AGENT="User-Agent: Reddit2Tube/1.0 by YOUR-REDDIT-USERNAME"

# Youtube
SCOPES='YOUR-COMMA-SEPARATED-LIST-OF-SCOPES"
API_SERVICE_NAME='youtube'
API_VERSION='v3'

# Run enviornment
RUN_ENV
```

### Database
Create database to track already uploaded videos. 

```commandline
# In command-line:

sqlite3 db.sqlite3 'CREATE TABLE IF NOT EXISTS uploaded_videos (id INTEGER PRIMARY KEY AUTOINCREMENT, video_id TEXT UNIQUE, upload_datetime DATETIME DEFAULT CURRENT_TIMESTAMP);'

```

### Customising YouTube Tiles and Descriptions with Templates

With the ability to define title and description variables based on the attributes of the `praw` submission object, users can ensure that their YouTube uploads are personalized and informative, enhancing their content creation and sharing experience.

Example of `templates/title.txt`
```commandline
"{title}" by {author}

```
 Example of templates/description.txt
```commandline
This video was posted by {author}.
```

### Usage

```
usage: Reddit2Tube.py [-h] [--subreddit_name SUBREDDIT_NAME] [--reddit_num_submissions REDDIT_NUM_SUBMISSIONS] [--time_filter TIME_FILTER] [--category CATEGORY] [--privacy_status PRIVACY_STATUS]

Download and upload top Reddit videos to YouTube.

optional arguments:
  -h, --help            show this help message and exit
  --subreddit_name SUBREDDIT_NAME
                        Name of the subreddit
  --reddit_num_submissions REDDIT_NUM_SUBMISSIONS
                        Number of Reddit submissions to process
  --time_filter TIME_FILTER
                        Time filter for Reddit submissions (e.g., "day", "week")
  --category CATEGORY   YouTube video category
  --privacy_status PRIVACY_STATUS
                        YouTube video privacy status (e.g., "private", "public")
```

Example: Upload to YouTube the top 3 videos of the week from r/Cats.

```commandline
python Reddit2Tube.py \
  --subreddit_name "cats" \
  --reddit_num_submissions 3 \
  --time_filter "week" \
  --privacy_status "private"

```

### TO-DO
- Create a module to clean downloaded titles


---


### Copyright and license
Copyright © 2023 Roperi. MIT License.