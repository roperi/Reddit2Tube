from reddit2tube.logging_config import configure_logging


def test_configure_logging_writes_rotating_log(tmp_path):
    log_file = tmp_path / "log" / "application.log"
    logger = configure_logging(log_file)
    logger.info("hello from test")
    for handler in logger.handlers:
        handler.flush()
    assert "hello from test" in log_file.read_text(encoding="utf-8")
