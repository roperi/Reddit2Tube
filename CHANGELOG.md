# Changelog

All notable changes to Reddit2Tube are documented here.

The project currently uses an `Unreleased` section while the modernization is
being prepared for its next tagged release.

## [Unreleased]

### Added

- Resumable-upload diagnostics, media validation, quota guards, and an opt-in
  troubleshooting upload profile.
- Proper Python package structure with editable installation support.
- Validated environment-based configuration and example configuration files.
- Automatic SQLite initialization and idempotent upload tracking.
- Offline-first test suite covering configuration, persistence, integrations,
  orchestration, CLI behavior, and failure paths.
- Ruff formatting and linting with an 80% core coverage gate.
- GitHub Actions CI across Python 3.10 through 3.13.
- Makefile commands for installation, formatting, linting, testing, coverage,
  and the complete quality gate.
- Pre-commit and pre-push hooks managed through the pre-commit framework.
- Contributor, security, and example-template documentation.

### Changed

- Switched dependency management, local development commands, hooks, and CI
  to uv with a committed lockfile.
- Removed the legacy requirements files; uv is now the supported installation
  workflow.
- Refactored Reddit, yt-dlp, YouTube, persistence, and workflow logic into
  testable boundaries.
- Improved CLI validation, error reporting, exit codes, and run summaries.
- Added safer download filename handling and configurable download paths.
- Centralized application logging with rotating log files.
- Reworked the README around quick start, configuration, operations, and local
  development workflows.
- Preserved compatibility with the original `Reddit2Tube.py`, `utils.py`, and
  `src.*` import paths.

### Security

- Added explicit guidance for protecting credentials, OAuth tokens, cookies,
  databases, logs, and downloaded media.
- Kept runtime secrets and generated artifacts outside version control.
