"""Backward-compatible script entry point."""

from reddit2tube.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
