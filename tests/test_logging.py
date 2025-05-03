"""Tests for logging functionality in the upstox_instrument_query package."""

import os
import shutil
import tempfile
from unittest.mock import patch

import pytest

from upstox_instrument_query.logging_config import (
    LOG_FILES,
    archive_logs,
    clean_old_archives,
    clear_logs,
    configure_logging,
    get_logger,
)


@pytest.fixture
def temp_log_dir():
    """Create a temporary log directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir

    shutil.rmtree(temp_dir)


def test_get_logger():
    """Test that get_logger returns a properly configured logger."""
    logger = get_logger("test")
    assert logger.name == "upstox_instrument_query.test"

    assert len(logger.handlers) > 0

    assert logger.level > 0


def test_configure_logging(temp_log_dir):
    """Test that configure_logging properly configures loggers."""
    loggers = configure_logging(log_dir=temp_log_dir, log_level="DEBUG")

    assert "main" in loggers
    assert "database" in loggers
    assert "api" in loggers
    assert "query" in loggers

    for name, log_filename in LOG_FILES.items():
        log_file = os.path.join(temp_log_dir, log_filename)
        assert os.path.exists(log_file)


def test_clear_logs(temp_log_dir):
    """Test that clear_logs properly clears log files."""

    configure_logging(log_dir=temp_log_dir)

    logger = get_logger("main", log_dir=temp_log_dir)
    logger.info("Test log message")

    log_file = os.path.join(temp_log_dir, "upstox_query.log")
    assert os.path.getsize(log_file) > 0

    cleared_files = clear_logs(log_dir=temp_log_dir)

    assert len(cleared_files) > 0
    assert os.path.getsize(log_file) == 0


def test_clear_specific_log(temp_log_dir):
    """Test clearing a specific log file."""

    configure_logging(log_dir=temp_log_dir)

    main_logger = get_logger("main", log_dir=temp_log_dir)
    db_logger = get_logger("database", log_dir=temp_log_dir)

    main_logger.info("Test main log message")
    db_logger.info("Test database log message")

    main_log = os.path.join(temp_log_dir, "upstox_query.log")
    db_log = os.path.join(temp_log_dir, "database.log")

    assert os.path.getsize(main_log) > 0
    assert os.path.getsize(db_log) > 0

    cleared_files = clear_logs(log_name="database", log_dir=temp_log_dir)

    assert len(cleared_files) == 1
    assert os.path.getsize(main_log) > 0
    assert os.path.getsize(db_log) == 0


def test_archive_logs(temp_log_dir):
    """Test archiving log files."""

    configure_logging(log_dir=temp_log_dir)
    logger = get_logger("main", log_dir=temp_log_dir)
    logger.info("Test log message for archiving")

    archive_path = archive_logs(log_dir=temp_log_dir)

    assert os.path.exists(archive_path)
    assert archive_path.endswith(".zip")


def test_clean_old_archives(temp_log_dir):
    """Test cleaning old archive files."""

    archive_dir = os.path.join(temp_log_dir, "archives")
    os.makedirs(archive_dir, exist_ok=True)

    dummy_archive = os.path.join(archive_dir, "logs_archive_dummy.zip")
    with open(dummy_archive, "w") as f:
        f.write("dummy archive content")

    with patch("os.path.getmtime", return_value=0):
        removed_files = clean_old_archives(log_dir=temp_log_dir, days=1)

    assert len(removed_files) == 1
    assert not os.path.exists(dummy_archive)
