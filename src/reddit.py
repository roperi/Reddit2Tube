import praw


def authenticate_reddit(reddit_client_id, reddit_client_secret, reddit_user_agent, reddit_username, reddit_password):
    """Authenticate and return a Reddit instance."""
    # Set your Reddit API credentials
    reddit = praw.Reddit(
        client_id=reddit_client_id,
        client_secret=reddit_client_secret,
        user_agent=reddit_user_agent,
        username=reddit_username,
        password=reddit_password
    )
    return reddit


def get_top_submissions(reddit, subreddit_name, num_submissions, time_filter):
    """Get the top submissions from a subreddit."""
    subreddit = reddit.subreddit(subreddit_name)
    top_submissions = subreddit.top(time_filter=time_filter, limit=int(num_submissions))
    return top_submissions
