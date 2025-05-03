"""Tests for the interactive query module.

This module tests the interactive command-line interface.
"""

import io
from unittest import mock

import pytest

from upstox_instrument_query.interactive import InteractiveQuery


@pytest.fixture
def mock_query_instance():
    """Fixture providing a mock InstrumentQuery instance."""
    with mock.patch(
        "upstox_instrument_query.interactive.InstrumentQuery"
    ) as mock_query_cls:
        mock_instance = mock.MagicMock()
        mock_query_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def interactive_instance(mock_query_instance):
    """Fixture providing an InteractiveQuery instance with mocked dependencies."""
    return InteractiveQuery("test.db")


def test_interactive_init(mock_query_instance):
    """Test InteractiveQuery initialization."""
    instance = InteractiveQuery("test.db")
    assert instance.query is mock_query_instance
    assert instance.last_results == []


def test_do_exit(interactive_instance):
    """Test exit command."""
    with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
        result = interactive_instance.do_exit("")
        assert result is True
        assert "Goodbye" in fake_out.getvalue()


def test_do_find(interactive_instance, mock_query_instance):
    """Test find command."""

    mock_query_instance.search_by_name.return_value = [
        {
            "instrument_key": "NSE_EQ|TEST1",
            "name": "Test Company 1",
            "trading_symbol": "TEST1",
            "exchange": "NSE",
            "instrument_type": "EQUITY",
        }
    ]

    with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
        interactive_instance.do_find("TEST")
        output = fake_out.getvalue()

        mock_query_instance.search_by_name.assert_called_once_with(
            "TEST", case_sensitive=False
        )

        assert "Found 1 results" in output
        assert "TEST1" in output

    with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
        interactive_instance.do_find("")
        output = fake_out.getvalue()
        assert "Error: Missing name pattern" in output


def test_do_exchange(interactive_instance, mock_query_instance):
    """Test exchange command."""

    mock_query_instance.filter_by_exchange.return_value = [
        {
            "instrument_key": "NSE_EQ|TEST1",
            "name": "Test Company 1",
            "trading_symbol": "TEST1",
            "exchange": "NSE",
            "instrument_type": "EQUITY",
        }
    ]

    with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
        interactive_instance.do_exchange("NSE")
        output = fake_out.getvalue()

        mock_query_instance.filter_by_exchange.assert_called_once_with("NSE")

        assert "Found 1 results" in output
        assert "NSE" in output


def test_do_symbol(interactive_instance, mock_query_instance):
    """Test symbol command."""

    mock_query_instance.get_by_trading_symbol.return_value = {
        "instrument_key": "NSE_EQ|TEST1",
        "name": "Test Company 1",
        "trading_symbol": "TEST1",
        "exchange": "NSE",
        "instrument_type": "EQUITY",
    }

    with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
        interactive_instance.do_symbol("TEST1")
        output = fake_out.getvalue()

        mock_query_instance.get_by_trading_symbol.assert_called_once_with(
            "TEST1", exchange=None
        )

        assert "Found 1 results" in output
        assert "TEST1" in output

    with mock.patch("sys.stdout", new=io.StringIO()):
        interactive_instance.do_symbol("TEST1 NSE")

        mock_query_instance.get_by_trading_symbol.assert_called_with(
            "TEST1", exchange="NSE"
        )


def test_do_isin(interactive_instance, mock_query_instance):
    """Test isin command."""

    mock_query_instance.filter_by_isin.return_value = [
        {
            "instrument_key": "NSE_EQ|TEST1",
            "name": "Test Company 1",
            "trading_symbol": "TEST1",
            "exchange": "NSE",
            "instrument_type": "EQUITY",
            "isin": "INE000A01001",
        }
    ]

    with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
        interactive_instance.do_isin("INE000A01001")
        output = fake_out.getvalue()

        mock_query_instance.filter_by_isin.assert_called_once_with("INE000A01001")

        assert "Found 1 results" in output


def test_do_custom(interactive_instance, mock_query_instance):
    """Test custom query command."""

    mock_query_instance.custom_query.return_value = [
        {
            "instrument_key": "NSE_EQ|TEST1",
            "name": "Test Company 1",
            "trading_symbol": "TEST1",
            "exchange": "NSE",
            "instrument_type": "EQUITY",
        }
    ]

    with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
        interactive_instance.do_custom('"exchange = ? AND name LIKE ?" NSE "%Test%"')
        output = fake_out.getvalue()

        mock_query_instance.custom_query.assert_called_once()
        args, kwargs = mock_query_instance.custom_query.call_args

        assert args[0] == "exchange = ? AND name LIKE ?"
        assert len(args[1]) == 2
        assert args[1][0] == "NSE"
        assert "%Test%" in args[1][1]

        assert "Found 1 results" in output

    mock_query_instance.custom_query.reset_mock()

    with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
        interactive_instance.do_custom('exchange = ? AND name LIKE ? NSE "%Test%"')
        output = fake_out.getvalue()

        mock_query_instance.custom_query.assert_called_once()


def test_do_ticker(interactive_instance):
    """Test ticker command."""

    with (
        mock.patch(
            "upstox_instrument_query.interactive.get_ticker_info"
        ) as mock_get_ticker,
        mock.patch(
            "upstox_instrument_query.interactive.display_ticker_info"
        ) as mock_display,
        mock.patch("sys.stdout", new=io.StringIO()) as fake_out,
    ):

        mock_ticker_info = {"symbol": "AAPL", "shortName": "Apple Inc."}
        mock_get_ticker.return_value = mock_ticker_info

        interactive_instance.query.search_by_name.return_value = [
            {"name": "APPLE INC", "trading_symbol": "AAPL", "exchange": "NSE"}
        ]

        interactive_instance.do_ticker("AAPL")

        mock_get_ticker.assert_called_once_with("AAPL")
        mock_display.assert_called_once_with(mock_ticker_info)

        mock_get_ticker.reset_mock()
        mock_display.reset_mock()

        interactive_instance.do_ticker("")

        assert "Error: Missing ticker symbol" in fake_out.getvalue()
        mock_get_ticker.assert_not_called()
        mock_display.assert_not_called()


def test_display_results(interactive_instance):
    """Test displaying results."""

    results = [
        {
            "instrument_key": f"NSE_EQ|TEST{i}",
            "name": f"Test Company {i}",
            "trading_symbol": f"TEST{i}",
            "exchange": "NSE",
            "instrument_type": "EQUITY",
        }
        for i in range(1, 25)
    ]

    with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
        interactive_instance._display_results(results)
        output = fake_out.getvalue()

        assert "Found 24 results" in output
        assert "INSTRUMENT_KEY" in output
        assert "TEST1" in output
        assert "...and 4 more results" in output

    with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
        interactive_instance._display_results([])
        output = fake_out.getvalue()

        assert "No results found" in output


def test_display_detail(interactive_instance):
    """Test displaying detailed instrument information."""

    equity = {
        "instrument_key": "NSE_EQ|TEST1",
        "name": "Test Company 1",
        "trading_symbol": "TEST1",
        "exchange": "NSE",
        "instrument_type": "EQUITY",
        "segment": "EQ",
        "isin": "INE000A01001",
        "last_price": 100.50,
        "lot_size": 1,
        "tick_size": 0.05,
    }

    with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
        interactive_instance._display_detail(equity)
        output = fake_out.getvalue()

        assert "=== Instrument Details ===" in output
        assert "Instrument Key: NSE_EQ|TEST1" in output
        assert "Trading Symbol: TEST1" in output
        assert "Last Price: 100.5" in output

    option = {
        "instrument_key": "NSE_OPT|TEST1|20251231|CE|100",
        "name": "Test Company 1 CE 100",
        "trading_symbol": "TEST1CE100",
        "exchange": "NSE",
        "instrument_type": "OPTIONS",
        "segment": "OPT",
        "isin": "INE000A01001",
        "strike": 100.0,
        "option_type": "CE",
        "expiry": "2025-12-31",
        "lot_size": 100,
        "tick_size": 0.05,
    }

    with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
        interactive_instance._display_detail(option)
        output = fake_out.getvalue()

        assert "=== Instrument Details ===" in output
        assert "--- Option Specifics ---" in output
        assert "Option Type" in output
        assert "CE" in output
        assert "Strike" in output
        assert "100.0" in output


def test_do_detail(interactive_instance):
    """Test detail command."""

    interactive_instance.last_results = [
        {
            "instrument_key": "NSE_EQ|TEST1",
            "name": "Test Company 1",
            "trading_symbol": "TEST1",
        }
    ]

    with mock.patch.object(interactive_instance, "_display_detail") as mock_display:

        interactive_instance.do_detail("0")
        mock_display.assert_called_once_with(interactive_instance.last_results[0])

        with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
            interactive_instance.do_detail("100")
            output = fake_out.getvalue()
            assert "Error: Index out of range" in output

        interactive_instance.last_results = []
        with mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
            interactive_instance.do_detail("0")
            output = fake_out.getvalue()
            assert "No results available" in output
