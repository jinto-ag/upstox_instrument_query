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

    sys.argv = ["upstox_query", "init", sample_json_path, temp_db_path]

    with mock.patch("sys.stdout", new=mock.MagicMock()):
        main()

    import sqlite3

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM instruments")
    count = cursor.fetchone()[0]
    assert count == 5

    cursor.execute("PRAGMA table_info(instruments)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "isin" in columns
    assert "option_type" in columns
    assert "security_type" in columns

    conn.close()


def test_cli_update_command(cli_args, sample_json_path, temp_db_path):
    """Test the 'update' CLI command."""

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

    cursor.execute(
        """
        INSERT INTO instruments (instrument_key, exchange, name)
        VALUES (?, ?, ?)
        """,
        ("DUMMY", "TEST", "WILL BE DELETED"),
    )
    conn.commit()
    conn.close()

    sys.argv = ["upstox_query", "update", sample_json_path, temp_db_path]

    with mock.patch("sys.stdout", new=mock.MagicMock()):
        main()

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM instruments")
    count = cursor.fetchone()[0]
    assert count == 5

    cursor.execute("SELECT COUNT(*) FROM instruments WHERE exchange = ?", ("TEST",))
    count = cursor.fetchone()[0]
    assert count == 0

    cursor.execute("SELECT COUNT(*) FROM instruments WHERE option_type = ?", ("CE",))
    count = cursor.fetchone()[0]
    assert count == 1

    conn.close()


def test_cli_url_flag(cli_args, temp_db_path):
    """Test the '--url' flag for init and update commands."""
    url = "http://example.com/instruments.json"

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

        sys.argv = ["upstox_query", "init", url, temp_db_path, "--url"]

        with mock.patch("sys.stdout", new=mock.MagicMock()):
            main()

        mock_load.assert_called_once()

        sys.argv = ["upstox_query", "update", url, temp_db_path, "--url"]

        mock_load.reset_mock()

        with mock.patch("sys.stdout", new=mock.MagicMock()):
            main()

        mock_load.assert_called_once()


def test_cli_yfinance_command(cli_args, temp_db_path):
    """Test the Yahoo Finance ticker CLI command."""

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
            trading_symbol TEXT
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO instruments (instrument_key, exchange, instrument_type, name, trading_symbol)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("NSE_EQ|INE123A01011", "NSE", "EQ", "APPLE INC", "AAPL"),
    )
    conn.commit()
    conn.close()

    sys.argv = [
        "upstox_query",
        "--db-path",
        temp_db_path,
        "ticker",
        "AAPL",
        "--find-instruments",
    ]

    def ensure_db_exists(path):
        return temp_db_path

    with mock.patch(
        "upstox_instrument_query.cli.yfinance_command"
    ) as mock_yfinance_cmd:
        with mock.patch(
            "upstox_instrument_query.database.InstrumentDatabase.ensure_database_exists",
            side_effect=ensure_db_exists,
        ):

            with mock.patch("sys.stdout", new=mock.MagicMock()):
                main()

            mock_yfinance_cmd.assert_called_once()

            args = mock_yfinance_cmd.call_args[0][0]
            assert args.ticker == "AAPL"
            assert args.find_instruments is True


def test_cli_yfinance_command_no_ticker(cli_args, temp_db_path):
    """Test the Yahoo Finance ticker CLI command when no ticker data is found."""

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
            trading_symbol TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    sys.argv = ["upstox_query", "--db-path", temp_db_path, "ticker", "INVALID"]

    def ensure_db_exists(path):
        return temp_db_path

    def mock_yfinance_command_side_effect(args):

        from upstox_instrument_query.yfinance import (
            display_ticker_info,
            get_ticker_info,
        )

        ticker_info = get_ticker_info(args.ticker)
        display_ticker_info(ticker_info)

        sys.exit(1)

    with mock.patch(
        "upstox_instrument_query.cli.yfinance_command",
        side_effect=mock_yfinance_command_side_effect,
    ) as mock_yfinance_cmd:
        with mock.patch(
            "upstox_instrument_query.database.InstrumentDatabase.ensure_database_exists",
            side_effect=ensure_db_exists,
        ):
            with mock.patch(
                "upstox_instrument_query.yfinance.get_ticker_info", return_value=None
            ) as mock_get_ticker:
                with mock.patch(
                    "upstox_instrument_query.yfinance.display_ticker_info"
                ) as mock_display_ticker:

                    with pytest.raises(SystemExit) as exc_info:
                        with mock.patch("sys.stdout", new=mock.MagicMock()):
                            main()

                    assert exc_info.value.code == 1

                    mock_yfinance_cmd.assert_called_once()
                    mock_get_ticker.assert_called_once_with("INVALID")
                    mock_display_ticker.assert_called_once_with(None)


def test_cli_error_handling(cli_args):
    """Test error handling in the CLI."""

    invalid_db = "/nonexistent/path/db.sqlite"
    sys.argv = ["upstox_query", "init", "invalid.json", invalid_db]

    with pytest.raises(SystemExit) as exc_info:
        with mock.patch("sys.stderr", new=mock.MagicMock()):
            main()

    assert exc_info.value.code == 1

    sys.argv = ["upstox_query", "update", "invalid.json", invalid_db]

    with pytest.raises(SystemExit) as exc_info:
        with mock.patch("sys.stderr", new=mock.MagicMock()):
            main()

    assert exc_info.value.code == 1

    sys.argv = ["upstox_query", "--db-path", invalid_db, "ticker", "AAPL"]

    with mock.patch("upstox_instrument_query.cli.InstrumentDatabase") as mock_db:

        mock_db.ensure_database_exists.return_value = invalid_db
        mock_db.side_effect = Exception("Database error: Unable to access database")

        with mock.patch("sys.stderr", new=mock.MagicMock()):

            with pytest.raises(SystemExit) as exc_info:
                from upstox_instrument_query.cli import yfinance_command

                args = type("args", (), {})()
                args.db_path = invalid_db
                args.ticker = "AAPL"
                args.find_instruments = False
                yfinance_command(args)

    assert exc_info.value.code == 1


def test_cli_help(cli_args):
    """Test the help output."""

    sys.argv = ["upstox_query"]

    with pytest.raises(SystemExit) as exc_info:
        with mock.patch("sys.stdout", new=mock.MagicMock()):
            main()

    assert exc_info.value.code == 0
