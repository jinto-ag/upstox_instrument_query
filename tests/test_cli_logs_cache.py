"""Tests for the CLI log and cache management commands."""

from unittest.mock import MagicMock, patch

import pytest

from upstox_instrument_query.cli import cache_command, logs_command


@pytest.fixture
def mock_args():
    """Create a mock args object for testing CLI commands."""

    class Args:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    return Args


def test_logs_clear_command(mock_args):
    """Test the logs clear command."""
    args = mock_args(clear=True, archive=False, clean_archives=False, log_name=None)

    with (
        patch("upstox_instrument_query.cli.clear_logs") as mock_clear_logs,
        patch("upstox_instrument_query.cli.logger"),
    ):

        mock_clear_logs.return_value = ["/path/to/log1.log", "/path/to/log2.log"]

        with patch("upstox_instrument_query.cli.print") as mock_print:
            logs_command(args)

        mock_clear_logs.assert_called_once_with(None)

        mock_print.assert_any_call("Cleared 2 log files")


def test_logs_archive_command(mock_args):
    """Test the logs archive command."""
    args = mock_args(clear=False, archive=True, clean_archives=False)

    with (
        patch("upstox_instrument_query.cli.archive_logs") as mock_archive_logs,
        patch("upstox_instrument_query.cli.logger"),
    ):

        mock_archive_logs.return_value = "/path/to/archive.zip"

        with patch("upstox_instrument_query.cli.print") as mock_print:
            logs_command(args)

        mock_archive_logs.assert_called_once()

        mock_print.assert_any_call("Logs archived to: /path/to/archive.zip")


def test_logs_clean_archives_command(mock_args):
    """Test the logs clean-archives command."""
    args = mock_args(clear=False, archive=False, clean_archives=True, days=15)

    with (
        patch("upstox_instrument_query.cli.clean_old_archives") as mock_clean_archives,
        patch("upstox_instrument_query.cli.logger"),
    ):

        mock_clean_archives.return_value = ["/path/to/old_archive.zip"]

        with patch("upstox_instrument_query.cli.print") as mock_print:
            logs_command(args)

        mock_clean_archives.assert_called_once_with(days=15)

        mock_print.assert_any_call("Removed 1 old archive files")


def test_cache_command(mock_args):
    """Test the cache clear command."""
    args = mock_args(db_path="/path/to/db.sqlite")

    with (
        patch("upstox_instrument_query.cli.InstrumentDatabase") as mock_db_class,
        patch("upstox_instrument_query.cli.InstrumentQuery") as mock_query_class,
        patch("upstox_instrument_query.cli.logger"),
    ):

        mock_db_class.ensure_database_exists.return_value = "/path/to/db.sqlite"
        mock_query_instance = MagicMock()
        mock_query_class.return_value = mock_query_instance

        with patch("upstox_instrument_query.cli.print") as mock_print:
            cache_command(args)

        mock_query_instance.clear_cache.assert_called_once()

        mock_print.assert_any_call("Query cache cleared successfully")
