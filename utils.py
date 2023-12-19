# Function to read templates from a file
def read_templates(file_path):
    with open(file_path, 'r') as template_file:
        content = template_file.read()
    return content.strip()


def generate_updated_info(submission, title_template, description_template):
    # Create a dictionary of submission attributes
    submission_info = {
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
    }

    # Format the title and description templates using the submission_info dictionary
    new_title = title_template.format(**submission_info)
    new_description = description_template.format(**submission_info)

    return new_title, new_description
