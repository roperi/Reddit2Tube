"""Compatibility helpers for older imports."""

from reddit2tube.templates import read_template, render_templates


def read_templates(file_path):
    return read_template(file_path)


def generate_updated_info(submission, title_template, description_template):
    return render_templates(submission, title_template, description_template)
