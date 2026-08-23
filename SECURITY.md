# Security

Reddit2Tube handles Reddit credentials, browser cookies, and YouTube OAuth
tokens. Keep `.env`, `config/`, cookie files, downloaded media, databases, and
logs outside version control. The repository ignores the usual runtime paths,
but always verify `git status` before publishing changes.

If you discover a security issue, do not publish credentials or exploit details
in an issue. Contact the repository owner privately with reproduction steps and
the affected version.
