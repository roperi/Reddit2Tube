# Contributing

Install uv using the instructions at
<https://docs.astral.sh/uv/getting-started/installation/>, then install the
development dependencies:

```bash
make install
make install-hooks
```

The project environment is managed by uv in `.venv/`. Use `uv run --locked`
for commands that are not exposed by the Makefile.

Before opening a pull request, run:

```bash
make check
```

Tests must be offline. Do not commit Reddit credentials, YouTube OAuth files,
cookies, databases, downloaded media, or log files.

Useful commands:

```bash
make help          # list available commands
make format        # apply Ruff formatting
make hooks-check   # run all pre-commit hooks manually
```

The pre-commit hook runs fast Ruff checks before commits. The pre-push hook
runs the complete test and coverage suite. GitHub Actions remains the
authoritative quality gate because hooks can be skipped or may not be
installed.
