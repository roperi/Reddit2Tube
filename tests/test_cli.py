from reddit2tube import cli
from reddit2tube.config import ConfigurationError
from reddit2tube.models import RunSummary


def test_main_without_subreddit_prints_help(capsys):
    assert cli.main([]) == 0
    assert "Download and upload" in capsys.readouterr().out


def test_main_returns_two_for_invalid_configuration(monkeypatch):
    monkeypatch.setattr(
        cli,
        "load_settings",
        lambda: (_ for _ in ()).throw(ConfigurationError("missing setting")),
    )
    assert cli.main(["--subreddit_name", "cats"]) == 2


def test_main_returns_one_when_workflow_has_failures(monkeypatch, settings):
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr(cli, "run_workflow", lambda *args, **kwargs: RunSummary(failures=1))
    assert cli.main(["--subreddit_name", "cats"]) == 1


def test_main_returns_zero_for_successful_workflow(monkeypatch, settings):
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr(cli, "run_workflow", lambda *args, **kwargs: RunSummary(uploaded=1))
    assert cli.main(["--subreddit_name", "cats", "--verbose"]) == 0


def test_main_returns_one_for_unexpected_workflow_error(monkeypatch, settings):
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr(
        cli,
        "run_workflow",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("network down")),
    )
    assert cli.main(["--subreddit_name", "cats"]) == 1
