import importlib

import logging

from src.common.logging import get_logger, setup_logging
from src.common.exceptions import RecommendationError, ExternalServiceError


def test_setup_logging_and_get_logger_emit_record(caplog):
    # Ensure logging is configured
    setup_logging(level=logging.INFO)
    logger = get_logger("test_logger")

    with caplog.at_level(logging.INFO):
        logger.info("phase6 test message")

    assert any("phase6 test message" in record.message for record in caplog.records)


def test_custom_exceptions_str():
    err = RecommendationError("something went wrong")
    ext_err = ExternalServiceError("groq failed")

    assert "something went wrong" in str(err)
    assert "groq failed" in str(ext_err)


def test_settings_reads_env_for_groq_key(monkeypatch):
    # Reload the settings module after changing env, so BaseSettings picks up the new value.
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")

    settings_module = importlib.import_module("src.config.settings")
    importlib.reload(settings_module)
    from src.config.settings import settings  # type: ignore  # re-import after reload

    assert settings.groq_api_key == "test-groq-key"

