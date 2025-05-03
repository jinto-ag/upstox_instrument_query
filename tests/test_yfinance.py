"""Tests for the YFinance module.

This module tests the YFinance integration functionality.
"""

from unittest import mock

import pytest

from upstox_instrument_query.yfinance import (
    display_corresponding_instruments,
    display_ticker_info,
    find_corresponding_instrument,
    get_ticker_info,
)


@pytest.fixture
def mock_yf():
    """Fixture to mock yfinance module."""
    with mock.patch("upstox_instrument_query.yfinance.yf", create=True) as mock_yf:
        yield mock_yf


@pytest.fixture
def sample_ticker_info():
    """Fixture to provide sample ticker information."""
    return {
        "symbol": "AAPL",
        "shortName": "Apple Inc.",
        "regularMarketPrice": 150.0,
        "exchange": "NMS",
        "regularMarketPreviousClose": 148.5,
        "regularMarketOpen": 149.0,
        "regularMarketDayLow": 148.0,
        "regularMarketDayHigh": 151.0,
        "fiftyTwoWeekLow": 120.0,
        "fiftyTwoWeekHigh": 180.0,
        "marketCap": 2500000000000,
        "regularMarketVolume": 75000000,
        "trailingPE": 25.5,
        "dividendYield": 0.007,
    }


@pytest.fixture
def sample_instruments():
    """Fixture to provide sample instruments for testing."""
    return [
        {
            "instrument_key": "NSE_EQ|INE123A01011",
            "name": "APPLE INC",
            "trading_symbol": "AAPL",
            "exchange": "NSE",
            "instrument_type": "EQ",
            "isin": "INE123A01011",
            "lot_size": 1,
            "tick_size": 0.05,
        },
        {
            "instrument_key": "NSE_FO|INE123A01011",
            "name": "APPLE INC",
            "trading_symbol": "AAPL",
            "exchange": "NSE",
            "instrument_type": "FUTURES",
            "isin": "INE123A01011",
            "expiry": "2025-05-29",
            "lot_size": 100,
        },
        {
            "instrument_key": "NSE_OPT|INE123A01011|CE|900",
            "name": "APPLE INC",
            "trading_symbol": "AAPL25MAY900CE",
            "exchange": "NSE",
            "instrument_type": "CE",
            "isin": "INE123A01011",
            "expiry": "2025-05-29",
            "strike": 900,
            "option_type": "CE",
            "lot_size": 100,
        },
        {
            "instrument_key": "NSE_OPT|INE123A01011|PE|900",
            "name": "APPLE INC",
            "trading_symbol": "AAPL25MAY900PE",
            "exchange": "NSE",
            "instrument_type": "PE",
            "isin": "INE123A01011",
            "expiry": "2025-05-29",
            "strike": 900,
            "option_type": "PE",
            "lot_size": 100,
        },
    ]


def test_get_ticker_info_success(mock_yf):
    """Test retrieving ticker information when successful."""

    mock_ticker = mock.MagicMock()
    mock_ticker.info = {
        "symbol": "AAPL",
        "shortName": "Apple Inc.",
        "regularMarketPrice": 150.0,
        "exchange": "NMS",
        "regularMarketPreviousClose": 148.5,
        "regularMarketOpen": 149.0,
        "regularMarketDayLow": 148.0,
        "regularMarketDayHigh": 151.0,
        "fiftyTwoWeekLow": 120.0,
        "fiftyTwoWeekHigh": 180.0,
        "marketCap": 2500000000000,
        "regularMarketVolume": 75000000,
        "trailingPE": 25.5,
        "dividendYield": 0.007,
    }
    mock_yf.Ticker.return_value = mock_ticker

    result = get_ticker_info("AAPL")

    assert result is not None
    assert result["symbol"] == "AAPL"
    assert result["shortName"] == "Apple Inc."
    assert result["regularMarketPrice"] == 150.0
    mock_yf.Ticker.assert_called_once_with("AAPL")


def test_get_ticker_info_failure(mock_yf):
    """Test handling of failed ticker information retrieval."""

    mock_ticker = mock.MagicMock()
    mock_ticker.info = {}
    mock_yf.Ticker.return_value = mock_ticker

    result = get_ticker_info("INVALID")

    assert result is None
    mock_yf.Ticker.assert_called_once_with("INVALID")


def test_get_ticker_info_exception(mock_yf):
    """Test handling of exceptions during ticker retrieval."""

    mock_yf.Ticker.side_effect = Exception("API error")

    result = get_ticker_info("AAPL")

    assert result is None
    mock_yf.Ticker.assert_called_once_with("AAPL")


@mock.patch("upstox_instrument_query.yfinance.yf", None)
@mock.patch("upstox_instrument_query.yfinance.print")
@mock.patch("upstox_instrument_query.yfinance.logger")
def test_get_ticker_info_no_yfinance(mock_logger, mock_print):
    """Test behavior when yfinance package is not installed."""

    result = get_ticker_info("AAPL")

    assert result is None
    mock_logger.error.assert_called_once()
    mock_print.assert_called_once()
    assert "yfinance package not installed" in mock_print.call_args[0][0]


@mock.patch("upstox_instrument_query.yfinance.print")
@mock.patch("upstox_instrument_query.yfinance.datetime")
def test_display_ticker_info(mock_datetime, mock_print, sample_ticker_info):
    """Test displaying ticker information with date-time."""

    mock_now = mock.MagicMock()
    mock_now.strftime.return_value = "2025-05-03 12:34:56"
    mock_datetime.datetime.now.return_value = mock_now

    display_ticker_info(sample_ticker_info)

    assert mock_print.call_count > 5

    calls = [call[0][0] for call in mock_print.call_args_list]
    captured_output = "\n".join(str(call) for call in calls if isinstance(call, str))

    assert "Data as of: 2025-05-03 12:34:56" in captured_output
    assert "Apple Inc." in captured_output
    assert "AAPL" in captured_output
    assert "150.0" in captured_output


@mock.patch("upstox_instrument_query.yfinance.print")
def test_display_ticker_info_empty(mock_print):
    """Test displaying ticker information when none is available."""

    display_ticker_info(None)

    mock_print.assert_called_once_with("No ticker information available")


def test_find_corresponding_instrument():
    """Test finding corresponding instruments in Upstox database."""

    mock_query = mock.MagicMock()
    mock_query.search_by_name.return_value = [
        {"name": "APPLE INC", "trading_symbol": "AAPL", "exchange": "NSE"},
        {
            "name": "APPLE ELECTRONICS",
            "trading_symbol": "APEL",
            "exchange": "BSE",
        },
    ]
    mock_query.get_by_trading_symbol.return_value = {
        "name": "APPLE INC",
        "trading_symbol": "AAPL",
        "exchange": "NSE",
    }

    ticker_info = {
        "symbol": "AAPL.NS",
        "shortName": "Apple Inc.",
        "exchange": "NSE",
    }

    results = find_corresponding_instrument(mock_query, ticker_info)

    assert len(results) == 3
    mock_query.search_by_name.assert_called_once_with("Apple")
    mock_query.get_by_trading_symbol.assert_called_once_with("AAPL")


def test_find_corresponding_instrument_empty():
    """Test finding instruments with empty ticker info."""
    mock_query = mock.MagicMock()

    results = find_corresponding_instrument(mock_query, {})

    assert len(results) == 0
    mock_query.search_by_name.assert_not_called()
    mock_query.get_by_trading_symbol.assert_not_called()


def test_find_corresponding_instrument_no_matches():
    """Test finding instruments with no matches."""
    mock_query = mock.MagicMock()
    mock_query.search_by_name.return_value = []
    mock_query.get_by_trading_symbol.return_value = None

    ticker_info = {
        "symbol": "XYZ",
        "shortName": "Unknown Company",
        "exchange": "NSE",
    }

    results = find_corresponding_instrument(mock_query, ticker_info)

    assert len(results) == 0
    mock_query.search_by_name.assert_called_once_with("Unknown")
    mock_query.get_by_trading_symbol.assert_called_once_with("XYZ")


def test_find_corresponding_instrument_pure_symbol():
    """Test finding instruments with pure symbol search."""
    mock_query = mock.MagicMock()

    mock_query.search_by_name.side_effect = [
        [],
        [{"trading_symbol": "AAPL", "name": "APPLE INC"}],
    ]
    mock_query.get_by_trading_symbol.return_value = None

    ticker_info = {
        "symbol": "AAPL.NS",
        "shortName": "Apple Inc.",
        "exchange": "NSE",
    }

    results = find_corresponding_instrument(mock_query, ticker_info)

    assert len(results) == 1

    assert mock_query.search_by_name.call_args_list[1][0][0] == "^AAPL$"
    assert mock_query.search_by_name.call_args_list[1][1]["case_sensitive"] is False


def test_find_corresponding_instrument_no_company_name():
    """Test finding instruments when ticker has no company name."""
    mock_query = mock.MagicMock()

    ticker_info = {
        "symbol": "AAPL.NS",
        "exchange": "NSE",
    }

    results = find_corresponding_instrument(mock_query, ticker_info)

    assert len(results) == 0

    mock_query.search_by_name.assert_not_called()


@mock.patch("upstox_instrument_query.yfinance.print")
def test_display_corresponding_instruments_empty(mock_print):
    """Test displaying corresponding instruments when none are available."""

    display_corresponding_instruments([])

    mock_print.assert_called_once_with(
        "\nNo corresponding instruments found in Upstox database."
    )


@mock.patch("upstox_instrument_query.yfinance.print")
def test_display_corresponding_instruments(mock_print, sample_instruments):
    """Test displaying corresponding instruments in categorized format."""

    display_corresponding_instruments(sample_instruments)

    assert mock_print.call_count > 10

    calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
    captured_output = "\n".join(str(call) for call in calls if isinstance(call, str))

    assert "Corresponding Upstox Instruments:" in captured_output
    assert "Available Instrument Types:" in captured_output
    assert "== EQUITY ==" in captured_output
    assert "== FUTURES ==" in captured_output
    assert "== CE ==" in captured_output
    assert "== PE ==" in captured_output

    assert "NSE_EQ|INE123A01011" in captured_output

    assert "Strike Price:" in captured_output
    assert "Option Type:" in captured_output

    assert "Expiry:" in captured_output
    assert "Lot Size:" in captured_output


@mock.patch("upstox_instrument_query.yfinance.print")
def test_display_corresponding_instruments_equity_only(mock_print):
    """Test displaying corresponding instruments with only equity instruments."""

    equity_only = [
        {
            "instrument_key": "NSE_EQ|INE123A01011",
            "name": "APPLE INC",
            "trading_symbol": "AAPL",
            "exchange": "NSE",
            "instrument_type": "EQ",
            "isin": "INE123A01011",
            "lot_size": 1,
            "tick_size": 0.05,
        }
    ]

    display_corresponding_instruments(equity_only)

    calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
    captured_output = "\n".join(str(call) for call in calls if isinstance(call, str))

    assert "== EQUITY ==" in captured_output
    assert "Trading Symbol: AAPL" in captured_output
    assert "Exchange: NSE" in captured_output

    assert "== FUTURES ==" not in captured_output
    assert "== CE ==" not in captured_output
    assert "== PE ==" not in captured_output


@mock.patch("upstox_instrument_query.yfinance.print")
def test_display_corresponding_instruments_unknown_type(mock_print):
    """Test displaying corresponding instruments with unknown instrument type."""

    unknown_type = [
        {
            "instrument_key": "NSE_UNKNOWN|INE123A01011",
            "name": "APPLE INC",
            "trading_symbol": "AAPL",
            "exchange": "NSE",
            "instrument_type": "UNKNOWN_TYPE",
            "isin": "INE123A01011",
        }
    ]

    display_corresponding_instruments(unknown_type)

    calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
    captured_output = "\n".join(str(call) for call in calls if isinstance(call, str))

    assert "== UNKNOWN_TYPE ==" in captured_output
    assert "Trading Symbol: AAPL" in captured_output
