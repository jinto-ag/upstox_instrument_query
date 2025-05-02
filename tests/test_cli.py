"""Tests for the command-line interface module.

This module tests the CLI functionality for initializing and updating
the instrument database through the command line.
"""

import sys
from unittest import mock

import pytest

from upstox_instrument_query.cli import main


@pytest.fixture
def cli_args():
    """Save and restore sys.argv for CLI tests."""
    old_argv = sys.argv
    yield
    sys.argv = old_argv


def test_cli_init_command(cli_args, sample_json_path, temp_db_path):
    """Test the 'init' CLI command."""
    # Set up command line arguments
    sys.argv = ["upstox_query", "init", sample_json_path, temp_db_path]

    # Run the CLI command
    with mock.patch("sys.stdout", new=mock.MagicMock()):
        main()

    # Verify database was created and has data
    import sqlite3

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM instruments")
    count = cursor.fetchone()[0]
    assert count == 5  # Updated to 5 instruments with our new sample data

    # Check for new columns
    cursor.execute("PRAGMA table_info(instruments)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "isin" in columns
    assert "option_type" in columns
    assert "security_type" in columns

    conn.close()


def test_cli_update_command(cli_args, sample_json_path, temp_db_path):
    """Test the 'update' CLI command."""
    # Initialize the database first
    import sqlite3

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS instruments (
            instrument_key TEXT,
            exchange TEXT,
            instrument_type TEXT,
            name TEXT,
            lot_size INTEGER,
            expiry TEXT,
            strike REAL,
            tick_size REAL,
            segment TEXT,
            exchange_token TEXT,
            trading_symbol TEXT,
            short_name TEXT,
            isin TEXT,
            option_type TEXT,
            freeze_quantity REAL,
            security_type TEXT,
            last_price REAL
        )
        """
    )
    # Add a dummy instrument that will be deleted
    cursor.execute(
        """
        INSERT INTO instruments (instrument_key, exchange, name)
        VALUES (?, ?, ?)
        """,
        ("DUMMY", "TEST", "WILL BE DELETED"),
    )
    conn.commit()
    conn.close()

    # Set up command line arguments for update
    sys.argv = ["upstox_query", "update", sample_json_path, temp_db_path]

    # Run the CLI command
    with mock.patch("sys.stdout", new=mock.MagicMock()):
        main()

    # Verify database was updated
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    # Check the total count
    cursor.execute("SELECT COUNT(*) FROM instruments")
    count = cursor.fetchone()[0]
    assert count == 5  # Updated to 5 instruments

    # Verify the dummy record was replaced
    cursor.execute("SELECT COUNT(*) FROM instruments WHERE exchange = ?", ("TEST",))
    count = cursor.fetchone()[0]
    assert count == 0

    # Check that option instruments were added
    cursor.execute("SELECT COUNT(*) FROM instruments WHERE option_type = ?", ("CE",))
    count = cursor.fetchone()[0]
    assert count == 1

    conn.close()


def test_cli_url_flag(cli_args, temp_db_path):
    """Test the '--url' flag for init and update commands."""
    url = "http://example.com/instruments.json"

    # Mock the URL loader
    with mock.patch(
        "upstox_instrument_query.database.stream_json_from_url"
    ) as mock_load:
        mock_load.return_value = [
            {
                "instrument_key": "NSE_EQ|INE001A01036",
                "exchange": "NSE",
                "instrument_type": "EQUITY",
                "name": "TEST COMPANY",
            }
        ]

        # Set up command line arguments for init with URL
        sys.argv = ["upstox_query", "init", url, temp_db_path, "--url"]

        # Run the CLI command
        with mock.patch("sys.stdout", new=mock.MagicMock()):
            main()

        # Verify URL loader was called
        mock_load.assert_called_once()

        # Also test update with URL
        sys.argv = ["upstox_query", "update", url, temp_db_path, "--url"]

        # Reset the mock
        mock_load.reset_mock()

        # Run the update command
        with mock.patch("sys.stdout", new=mock.MagicMock()):
            main()

        # Verify URL loader was called again
        mock_load.assert_called_once()


def test_cli_error_handling(cli_args):
    """Test error handling in the CLI."""
    # Invalid database path
    invalid_db = "/nonexistent/path/db.sqlite"
    sys.argv = ["upstox_query", "init", "invalid.json", invalid_db]

    # The CLI should exit with a non-zero status
    with pytest.raises(SystemExit) as exc_info:
        with mock.patch("sys.stderr", new=mock.MagicMock()):
            main()

    assert exc_info.value.code == 1

    # Test error handling for update command
    sys.argv = ["upstox_query", "update", "invalid.json", invalid_db]

    with pytest.raises(SystemExit) as exc_info:
        with mock.patch("sys.stderr", new=mock.MagicMock()):
            main()

    assert exc_info.value.code == 1


def test_cli_help(cli_args):
    """Test the help output."""
    # No arguments should show help
    sys.argv = ["upstox_query"]

    # Should exit with zero status
    with pytest.raises(SystemExit) as exc_info:
        with mock.patch("sys.stdout", new=mock.MagicMock()):
            main()

    assert exc_info.value.code == 0
