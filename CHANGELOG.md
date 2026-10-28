# Changelog

All notable changes to Reddit2Tube are documented here.

The project currently uses an `Unreleased` section while the modernization is
being prepared for its next tagged release.

## [Unreleased]

### Added

- Durable tracking of uploads that are pending or failed, plus a `--retry-failed`
  mode that re-uploads them without depending on the Reddit listing.
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
- Documented resuming failed uploads with `--retry-failed`.
- Preserved compatibility with the original `Reddit2Tube.py`, `utils.py`, and
  `src.*` import paths.

### Fixed

- Reddit-hosted videos are now downloaded from the direct `v.redd.it` media URL
  returned by PRAW, avoiding yt-dlp's Reddit JSON metadata request. This fixes
  the `Your IP address is unable to access the Reddit API` failure on networks
  where the OAuth API works but `/comments/.../.json` is blocked. Pending rows
  recorded with a permalink are resolved the same way when retried.
- Resumable YouTube uploads no longer consume the retry budget on every
  successfully uploaded chunk, which previously failed any upload larger than
  `max_retries * chunk_size` (80 MiB with defaults) and added exponential
  backoff delays between successful chunks.

### Security

- Added explicit guidance for protecting credentials, OAuth tokens, cookies,
  databases, logs, and downloaded media.
- Kept runtime secrets and generated artifacts outside version control.
