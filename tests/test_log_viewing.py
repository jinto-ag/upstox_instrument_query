"""Tests for the log viewing functionality."""

import tempfile

import pytest

from upstox_instrument_query.logging_config import (
    LOG_FILES,
    configure_logging,
    get_logger,
    list_available_logs,
    view_logs,
)


@pytest.fixture
def temp_log_dir_with_content():
    """Create a temporary log directory with some log content for testing."""
    temp_dir = tempfile.mkdtemp()

    configure_logging(log_dir=temp_dir)

    main_logger = get_logger("main", log_dir=temp_dir)
    db_logger = get_logger("database", log_dir=temp_dir)

    for i in range(1, 21):
        main_logger.info(f"Test main log entry {i}")

    for i in range(1, 11):
        db_logger.info(f"Test database log entry {i}")
    db_logger.error("Test database error entry")

    yield temp_dir

    import shutil

    shutil.rmtree(temp_dir)


def test_view_logs_default(temp_log_dir_with_content):
    """Test viewing logs with default options."""
    log_lines = view_logs(log_dir=temp_log_dir_with_content)

    assert len(log_lines) > 0
    assert any("Test main log entry" in line for line in log_lines)


def test_view_logs_specific(temp_log_dir_with_content):
    """Test viewing a specific log."""
    log_lines = view_logs(log_name="database", log_dir=temp_log_dir_with_content)

    assert len(log_lines) > 0
    assert any("Test database log entry" in line for line in log_lines)
    assert any("Test database error entry" in line for line in log_lines)


def test_view_logs_head(temp_log_dir_with_content):
    """Test viewing the head of logs."""
    log_lines = view_logs(log_dir=temp_log_dir_with_content, head=5)

    assert len(log_lines) == 5


def test_view_logs_tail(temp_log_dir_with_content):
    """Test viewing the tail of logs."""
    log_lines = view_logs(log_dir=temp_log_dir_with_content, tail=5)

    assert len(log_lines) == 5


def test_view_logs_search(temp_log_dir_with_content):
    """Test searching in logs."""
    log_lines = view_logs(
        log_name="database", log_dir=temp_log_dir_with_content, search_pattern="error"
    )

    assert len(log_lines) > 0
    assert all("error" in line.lower() for line in log_lines)


def test_list_available_logs(temp_log_dir_with_content):
    """Test listing available logs."""
    log_files = list_available_logs(log_dir=temp_log_dir_with_content)

    assert set(log_files.keys()) == set(LOG_FILES.keys())

    for log_name, files in log_files.items():
        assert len(files) > 0
        assert "path" in files[0]
        assert "size" in files[0]
        assert "modified" in files[0]
