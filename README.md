<h1 align="center">Reddit2Tube</h1>
<h2 align="center">Automatically populate your YouTube channel with highly-rated Reddit videos</h2>

---

## Features

- Automate the process of downloading popular videos from public subreddits
- Simplify video uploads to your YouTube channel
- Streamline the process of creating titles and descriptions for your content using predefined templates


---

### Libraries 
- Praw
- yt_dlp
- google-auth et al
- google-api-python-client

### Requirements

- Python +3.8
- A YouTube Channel created with either a Google personal account (__NOT Recommended__) or with a Google Workspace or Google Identity account (__Highly Recommended__) 
- YouTube Data API v3 access 
- Reddit API access

---

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

__Using Reddit2Tube for personal use? Create a YouTube Channel using a Google Workspace (paid) or a Google Identity (free) account__  
If you are using Reddit2Tube for your own personal use I'd highly recommend you to NOT upload to the YouTube channel 
created with your personal Google account. Instead, create a new YouTube channel using a Google Workplace (paid) or 
Google Identity (free) account. 

__Why can't I use my YouTube channel created with my personal Google account?__   
You can but YouTube will place all your uploaded videos in locked mode (under review) until your app is verified. 
Since the app verification process could take weeks and requires some extra effort, it is only worth going through it 
only if you are planning to create an app that is going to be used by many users. Alternatively if you are using Reddit2Tube for personal 
use create a YouTube Channel with a Google Workspace or Google Identity account to start uploading videos programmatically right away. 

In general this is how you set up the YouTube API v3:

1. Log to your Google Cloud Console  https://console.cloud.google.com/
2. Create a project and name it
3. In `Enabled APIs and services`: 
   - Add YouTube Data API v3
4. In `Credentials` click API Key:
   - Create an API Key (and copy it somewhere as it is going to be used later on) 
5. Again in `Credentials` click OAuth client ID:
   - In application type select **Desktop client** to authenticate in your browser.
   - Click DOWNLOAD JSON to download the credentials and rename file to `client_secret.json`.
6. In `OAuth consent screen`:
   - Add Test user
     - In User type:
       - Select 'External' if your app is going to be used by many users (requires app verification)
       - Select 'Internal' if your app is going to be used only by you (no app verification). Note that you won't be able 
       to select `Internal` if you created the Google Cloud project with your Google Personal 
account (you need a Google Workspace or Google identity account in order to select this option).
   - Add scope: `https://www.googleapis.com/auth/youtube.upload`

__YouTube API v3 OAuth client credentials__

Create a `config` folder and put the json file containing the Client ID and Client Secret credentials inside it. Name it as `client_secret.json`. 

Example of copying the OAuth client credentials to the config folder:

```commandline
mkdir config/
cp /tmp/client_secret_1234556-3oiuoer3p939rsaqp.apps.googleusercontent.com.json ~/Reddit2Tube/config/client_secret.json
```

__Upload limit__  
You will have a quota limit of 10,000 queries a day (this is equivalent to uploading no more than 6 videos at a cost of 1600 queries per video). You can request a quota increase though.

---

## Installation

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
SCOPES='https://www.googleapis.com/auth/youtube.upload' # list of comma-separated scopes (in this case we are only using one scope)
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
usage: Reddit2Tube.py [-h] [--subreddit_name SUBREDDIT_NAME] [--reddit_num_submissions REDDIT_NUM_SUBMISSIONS] [--time_filter TIME_FILTER] [--category CATEGORY] [--privacy_status PRIVACY_STATUS] [--made_for_kids]
                      [--just_download]

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
                        YouTube video privacy status (e.g., "private", "public", "unlisted")
  --made_for_kids       Set if the video is made for kids
  --just_download       Skip YouTube uploading
```

__Usage example__  
Upload the top video of the day from _r/Cats_ to your YouTube channel.

```commandline
python Reddit2Tube.py \
  --subreddit_name "cats" \
  --reddit_num_submissions 1 \
  --time_filter "day" \
  --privacy_status "private" \
  --made_for_kids
```
Add the flag `--made_for_kids` if you want to make the video kid friendly. Otherwise, don't set this flag.  
To skip the YouTube upload part use the `--just_download` flag.


__Output example__
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

The first time you run Reddit2Tube, YouTube will ask you to _manually_ authenticate. You must grant permission to your app to be able to access your YouTube account. 

The file `config/token.json` stores your user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time. `config/token.json` will be used for the next run.  


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

Tip: One way I found to make it work was to pip install all the packages in `requirements.txt` except for the `google-api-core` one. Once the rest of the packages are installed, proceed to pip install `google-api-core`.

---

## Production

Once you are done with local development testing you can start using Reddit2Tube in a production server 
for total automation.

### Upload your local development files 
Upload your local .env, database, templates and credentials to the remote server via scp.

__Important__   
Make sure to run Reddit2Tube in your local development to force the creation of a refresh token so you won't be asked to authenticate in the remote server.

```commandline
# Assuming you git cloned Reddit2Tube in user's root folder.

mkdir templates/ config/
scp .env your-user@your-ip-address:"/home/your-user/Reddit2Tube/"
scp db.sqlite3 your-user@your-ip-address:"/home/your-user/Reddit2Tube/"
scp templates/* your-user@your-ip-address:"/home/your-user/Reddit2Tube/templates"
scp config/* your-user@your-ip-address:"/home/your-user/Reddit2Tube/config/"
```

### Bash script 
To automate the download/upload workflow you can use a bash script executed as a cron job.

In the project folder create a bin folder and create a Reddit2Tube.sh bash script in it.

It will log its output to `log/Reddit2Tube.log`.

```
mkdir bin/ log/
touch bin/Reddit2Tube.sh
```

Paste the following to `bin/Reddit2Tube.sh`

```

#!/bin/bash
#
# Execute `Reddit2Tube.py` module if it is not running.
#
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
parent="$(dirname "$DIR")"

if pgrep -f "Reddit2Tube.py" &>/dev/null; then
    :
else
    # Activate virtualenv
    source ~/.virtualenvs/Reddit2Tube/bin/activate
    # Run
    nohup ~/.virtualenvs/Reddit2Tube/bin/python $parent/Reddit2Tube.py --subreddit_name "cats" --reddit_num_submissions 3 --time_filter week --privacy_status private > $parent/log/Reddit2Tube.log  2>&1 &

fi

```

Note that the above script uploads the top 3 r/Cats videos of the week to your YouTube channel. Edit the script 
to suit your use case. 

Make it executable
```commandline
chmod +x bin/Reddit2Tube.sh
```

### Cron job

Create a cron job to execute the above script. 

Type `contab -e` and create a cron job that suits your needs. 

In the following example `Reddit2Tube.sh` will be executed 
once a week at 5:00am.

```commandline
0 5 * * 1 $HOME/Reddit2Tube/bin/Reddit2Tube.sh
```

Save the crontab and exit.

And that's it! The cron job will run once a week and upload the 3 most upvoted videos from r/Cats to your YouTube channel in private mode.

### Keep refreshing your tokens

Don't forget to get a new refresh token by running Reddit2Tube at local level and upload again your `config/token.json` to avoid being asked to authenticate
in the remote server. It seems refresh tokens last 7 days.

---

### Copyright and license
Copyright © 2023 Roperi. MIT License.
