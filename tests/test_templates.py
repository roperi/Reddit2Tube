from reddit2tube.templates import render_templates, submission_context


def test_render_templates_handles_deleted_author(submission):
    submission.author = None
    title, description = render_templates(submission, "{title} / {author}", "{url}")
    assert title == "A good cat video / [deleted]"
    assert description == "https://v.redd.it/example"


def test_long_titles_are_truncated_only_when_needed(submission):
    submission.title = "x" * 100
    context = submission_context(submission)
    assert len(context["title"]) == 70
    assert context["title"].endswith("...")
