# Contributing

Create a virtual environment and install the development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
make install
make install-hooks
```

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
