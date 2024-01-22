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
- Google account
- Access to YouTube Data API v3
- Verify your app with Google (optional)
- Reddit app credentials

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
     - Download the credentials as `client_secret.json`.
     - Use **Desktop client** to authenticate in your browser.
4. In `OAuth consent screen`:
   - Add Test user
   - Select 'External' in User type 


The client ID and its secret should be inside the config folder and named as `client_secret.json`. 

Example of copying the OAuth 2.0 client credentials to the config folder:

```commandline
mkdir config/
cp client_secret_1234556-3oiuoer3p939rsaqp.apps.googleusercontent.com.json ~/Reddit2Tube/config/client_secret.json
```


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
# Database
DATABASE_FILE='db.sqlite3'

# Reddit
REDDIT_CLIENT_ID="YOUR-REDDIT-CLIENT-ID"
REDDIT_CLIENT_SECRET="YOUR-REDDIT-SECRET"
REDDIT_USERNAME="YOUR-REDDIT_USERNAME"
REDDIT_PASSWORD="YOUR-REDDIT_PASSWORD"
REDDIT_USER_AGENT="User-Agent: Reddit2Tube/1.0 by YOUR-REDDIT-USERNAME"

# YouTube API V3
CLIENT_SECRETS_FILE='config/client_secret.json'
SCOPES='YOUR-COMMA-SEPARATED-LIST-OF-SCOPES"
API_SERVICE_NAME='youtube'
API_VERSION='v3'
```

### Database
Create database to keep track of the videos uploaded to YouTube (so it won't be uploaded again). 

In command-line:

```commandline
sqlite3 db.sqlite3 'CREATE TABLE IF NOT EXISTS uploaded_videos (id INTEGER PRIMARY KEY AUTOINCREMENT, video_id TEXT UNIQUE, title TEXT, upload_datetime DATETIME DEFAULT CURRENT_TIMESTAMP);'
```

### Customising YouTube Tiles and Descriptions with Templates

With the ability to define title and description variables based on the attributes of the `praw` submission object, users can ensure that their YouTube uploads are personalized and informative, enhancing their content creation and sharing experience.

Create a `templates` folder and put your title and description templates in there. 
```commandline
mkdir templates/
touch templates/title.txt
touch templats/description.txt
```
Content example of `templates/title.txt`
```commandline
"{title}" by {author}
```
 Content example of templates/description.txt
```commandline
This video was posted by {author}.
```
Submission attributes that can be used in both templates:
```commandline
'title': submission.title,
'id': submission.id,
'author': submission.name.author,
'selftext': submission.selftext,
'url': submission.url,
'score': submission.score,
'num_comments': submission.num_comments,
'created_utc': submission.created_utc,
'subreddit': submission.subreddit,
'is_self': submission.is_self,
'link_flair_text': submission.link_flair_text,
'locked': submission.locked,
```
### Logging
Downloads and uploads are logged in a file inside the `log` folder. 

Create log folder
```
mkdir log/
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
  --made_for_kids       Set if the video is made for kids

```

Example: Upload the top video of the day from r/Cats to your YouTube account.

```commandline
python Reddit2Tube.py \
  --subreddit_name "cats" \
  --reddit_num_submissions 1 \
  --time_filter "day" \
  --privacy_status "private" \
  --made_for_kids
```
Add the flag `--made_for_kids` if you want to make the video kid friendly. Otherwise, don't set this flag.

Output:
```commandline
[INFO. __main__, (line #72) - 2023-11-19 19:51:14,480] Authenticating with Reddit
[INFO. __main__, (line #102) - 2023-11-19 19:51:16,146] Downloading `Cat falls from sofa baby laughs` from `https://v.redd.it/t5dads5c77c1`
[generic] Extracting URL: https://v.redd.it/t5pdadsabo365c77c1
[generic] t5pbo365c77c1: Downloading webpage
[redirect] Following redirect to https://www.reddit.com/r/cats/comments/18law16c/cat_falls_sofa/?rdt=34051
[Reddit] Extracting URL: https://www.reddit.com/r/cats/comments/18law16c/cat_falls_sofa/?rdt=34051
[Reddit] 18law16c: Downloading JSON metadata
[Reddit] 18law16c: Downloading m3u8 information
[Reddit] 18law16c: Downloading MPD manifest
[info] t5pbo365c77c1: Downloading 1 format(s): fallback+dash-8
[download] Destination: /tmp/Cat falls from sofa baby laughs.ffallback.mp4
[download] 100% of   45.26MiB in 00:00:37 at 1.22MiB/s
[download] Destination: /tmp/Cat falls from sofa baby laughs.fdash-8.m4a
[download] 100% of    1.25MiB in 00:00:00 at 1.28MiB/s
[Merger] Merging formats into "/tmp/Cat falls from sofa baby laughs.mp4"
Deleting original file /tmp/Cat falls from sofa baby laughs.fdash-8.m4a (pass -k to keep)
Deleting original file /tmp/Cat falls from sofa baby laughs.ffallback.mp4 (pass -k to keep)
[INFO. __main__, (line #112) - 2023-11-19 19:52:07,891] Authenticating with Youtube
Please visit this URL to authorize this application: https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=1233454734-q1g9rahdshadioaud82vbp76mumtl.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube.upload&state=ud8a7jAHdaMnAsjdas9jdsaASD23&access_type=offline
Uploading file...
Uploading file...
Uploading file...
Uploading file...
Uploading file...
Uploading file...
Video id HN2Nv_5wJA was successfully uploaded
```

### YouTube Authentication & Authorization flow

The first time you run Reddit2Tube, YouTube will ask you to _manually_ authenticate. You must grant permission to Google Accounts to allow your app access. 

The file `config/token.json` stores your user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time. `config/token.json` will be used for the next run.  

**Verify your app with Google**

If your app isn't verified by Google, these tokens will be likely to be revoked almost immediately requiring you to authenticate every time you upload a video to YouTube.



### ModuleNotFoundError
If you get any of these errors:

```commandline
ModuleNotFoundError: No module named 'google.appengine'
or 
ModuleNotFoundError: No module named 'oauth2client'
or 
ImportError: file_cache is unavailable when using oauth2client >= 4.0.0 or google-auth

```
Reddit2Tube should still be able to upload to YouTube without any issues. These error messages are probably caused by the combined use of the following packages:
```commandline
google-auth-httplib2==0.1.0
google-api-python-client==1.7.8
httplib2==0.15.0
google-auth==1.12.0
```         
Finding the right combination to make YouTube uploads via the API is hard as you can see [here](https://stackoverflow.com/questions/59815620/gcloud-upload-httplib2-redirectmissinglocation-redirected-but-the-response-is-m).

Tip: One way I found to make the it work was to pip install all the packages in `requirements.txt` except for the `google-api-core` one. Once the rest of the packages are installed, proceed to pip install `google-api-core`.

---


### Copyright and license
Copyright © 2023 Roperi. MIT License.
