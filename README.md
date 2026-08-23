# Reddit2Tube

![CI](https://github.com/roperi/Reddit2Tube/actions/workflows/ci.yml/badge.svg)

Reddit2Tube is a Python automation tool that finds highly-rated videos in a
public subreddit, downloads them with `yt-dlp`, renders YouTube metadata from
templates, and optionally uploads the videos through the YouTube Data API.

The project is designed as a small, testable automation pipeline rather than a
hosted service. It is useful for learning and personal workflows, while still
demonstrating configuration validation, dependency injection, SQLite
idempotency, retries, logging, and offline testing.

## Workflow

```text
Reddit API -> filter video submissions -> render templates -> SQLite duplicate check
                                                        |
                                      yt-dlp download <-+
                                                        |
                                  YouTube upload (optional)
                                                        |
                                  record successful upload
```

In upload mode the application records a submission only after YouTube returns
an upload ID. Download-only runs intentionally do not mark a submission as
uploaded, so the same video can be uploaded later. This makes retries safe
when a run is interrupted or an upload fails.

## Requirements

- Python 3.10 or newer
- Reddit API credentials
- YouTube Data API v3 credentials for upload mode
- Permission to download and republish the selected content

Reddit2Tube does not bypass access controls. Respect Reddit, YouTube, and
content-owner terms, copyright, rate limits, and community rules.

## Quick start

```bash
git clone https://github.com/roperi/Reddit2Tube.git
cd Reddit2Tube
python -m venv .venv
source .venv/bin/activate
make install
make install-hooks
cp .env.example .env
mkdir -p templates
cp examples/templates/* templates/
```

Edit `.env` with your Reddit credentials. The application creates the SQLite
database, tables, log directory, and download directory automatically.

Run the test suite and inspect the CLI:

```bash
make check
python -m reddit2tube --help
```

## Configuration

`.env.example` is the complete configuration reference. The most important
values are:

| Variable | Purpose |
| --- | --- |
| `DATABASE_FILE` | SQLite file used to prevent duplicate processing |
| `DOWNLOAD_DIR` | Directory for downloaded media |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Reddit application credentials |
| `REDDIT_USERNAME` / `REDDIT_PASSWORD` | Reddit account used by PRAW |
| `REDDIT_USER_AGENT` | Descriptive Reddit API user agent |
| `CLIENT_SECRETS_FILE` | Google OAuth desktop-client JSON file |
| `SCOPES` | Comma-separated YouTube OAuth scopes |

For Reddit anti-bot challenges, configure exactly one of
`REDDIT_COOKIES_FROM_BROWSER` or `REDDIT_COOKIES_FILE`. Cookie contents are
never logged. Keep `.env`, `config/`, and cookie files private.

### Reddit credentials

Create a script application at <https://www.reddit.com/prefs/apps/> and copy
its client ID and secret into `.env`. Use a descriptive user agent such as:

```dotenv
REDDIT_USER_AGENT=Reddit2Tube/1.0 by your-reddit-username
```

### YouTube credentials

In Google Cloud:

1. Create or select a project.
2. Enable YouTube Data API v3.
3. Create an OAuth client ID for a desktop application.
4. Download the JSON file to `config/client_secret.json`.
5. Add the YouTube upload scope to the OAuth consent configuration.

The first upload run opens a browser for authorization. The resulting token is
stored under `config/` and is ignored by Git.

## Templates

Copy the examples into `templates/` and customize them:

```bash
mkdir -p templates
cp examples/templates/* templates/
```

Both templates use Python `str.format` fields. Available fields include:
`title`, `id`, `author`, `selftext`, `url`, `score`, `num_comments`,
`created_utc`, `subreddit`, `is_self`, `link_flair_text`, and `locked`.

Deleted Reddit accounts render as `[deleted]`. Titles longer than 70 characters
are shortened before template rendering.

## Usage

The original script entrypoint remains supported:

```bash
python Reddit2Tube.py \
  --subreddit_name cats \
  --reddit_num_submissions 1 \
  --time_filter day \
  --privacy_status private
```

The installed command and module entrypoints are equivalent:

```bash
reddit2tube --subreddit_name cats --reddit_num_submissions 1
python -m reddit2tube --subreddit_name cats --just_download
```

Useful options:

| Option | Default | Description |
| --- | --- | --- |
| `--subreddit_name` | — | Subreddit to query |
| `--reddit_num_submissions` | `2` | Number of top submissions to inspect |
| `--time_filter` | `day` | Reddit period, such as `day` or `week` |
| `--category` | `22` | YouTube category ID |
| `--privacy_status` | `private` | `private`, `unlisted`, or `public` |
| `--made_for_kids` | off | Set YouTube’s self-declared kids flag |
| `--just_download` | off | Skip YouTube authentication and upload |
| `--verbose` | off | Enable debug logging |

The process exits non-zero for invalid configuration or failed submissions.
Independent submissions continue to be attempted, and the final log includes a
run summary.

## Development

Install the project with its development tools:

```bash
make install
```

Run the complete local quality gate:

```bash
make check
```

The repository also provides `make format`, `make lint`, `make test`,
`make coverage`, and `make hooks-check` for individual checks. After
`make install-hooks`, Ruff runs before commits and the complete offline test
suite runs before pushes.

Tests are intentionally offline. Reddit, yt-dlp, and YouTube are isolated
behind injectable boundaries and replaced with fakes in workflow tests. CI
runs the quality gate on Python 3.10 through 3.13.

## Operations

For scheduled personal automation, call the installed command from cron or a
systemd timer with an absolute working directory and a private environment
file. Keep the process single-instance if multiple schedules could overlap.

Example cron entry:

```cron
0 5 * * 1 cd /path/to/Reddit2Tube && /path/to/Reddit2Tube/.venv/bin/reddit2tube --subreddit_name cats --reddit_num_submissions 3 --time_filter week --privacy_status private
```

Start with `private` or `unlisted` uploads while validating templates, quota,
and content policy. YouTube upload quota is finite and can make a failed retry
expensive.

## Security and repository hygiene

Never commit `.env`, OAuth client secrets, OAuth tokens, Reddit cookies,
databases, downloaded media, or logs. The repository ignores these runtime
artifacts and includes [SECURITY.md](SECURITY.md) with handling guidance.

Contributions should follow [CONTRIBUTING.md](CONTRIBUTING.md). See the
[CHANGELOG](CHANGELOG.md) for project evolution. The project is released under
the MIT license; see [LICENSE](LICENSE).
