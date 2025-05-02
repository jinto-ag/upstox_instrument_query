"""Tests for additional code coverage.

This module contains tests targeting specific lines and edge cases
to achieve 100% code coverage.
"""

import os
import sqlite3
import tempfile
from unittest import mock

from upstox_instrument_query.database import InstrumentDatabase
from upstox_instrument_query.query import InstrumentQuery
from upstox_instrument_query.utils import stream_json, stream_json_from_url


def test_database_methods_with_no_cursor():
    """Test the database methods when cursor is None."""
    db = InstrumentDatabase(":memory:")

    db._load_json("path/to/nonexistent/file.json")

    db._load_json_from_url("http://example.com/file.json")

    db._create_indexes()

    with mock.patch(
        "upstox_instrument_query.database.InstrumentDatabase.connect"
    ) as mock_connect:

        def mock_connect_impl():
            db.conn = mock.MagicMock()
            db.cursor = None

        mock_connect.side_effect = mock_connect_impl

        db.update_instruments("path/to/file.json")


def test_utils_dict_from_file():
    """Test handling a dictionary instead of a list in stream_json."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write('{"single": "object"}')
        temp_file = f.name

    try:
        results = list(stream_json(temp_file))
        assert len(results) == 1
        assert results[0]["single"] == "object"
    finally:
        os.unlink(temp_file)


def test_utils_stream_json_whitespace():
    """Test handling of whitespace in the stream_json function."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write('[{"id": 1} ,\n  \t {"id": 2}]')
        temp_file = f.name

    try:
        results = list(stream_json(temp_file))
        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2
    finally:
        os.unlink(temp_file)


def test_utils_stream_json_advanced_whitespace():
    """Test advanced whitespace handling in stream_json function."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write('[{"id": 1},\n\r\t {"id": 2},  \n{"id": 3}]')
        temp_file = f.name

    try:
        results = list(stream_json(temp_file))
        assert len(results) == 3
        assert [r["id"] for r in results] == [1, 2, 3]
    finally:
        os.unlink(temp_file)


@mock.patch("urllib.request.urlopen")
def test_utils_dict_from_url(mock_urlopen):
    """Test handling a dictionary from a URL stream."""
    mock_response = mock.MagicMock()
    mock_response.headers = {}
    mock_response.read.return_value = b'{"single": "object"}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    results = list(stream_json_from_url("http://example.com/data.json"))
    assert len(results) == 1
    assert results[0]["single"] == "object"


@mock.patch("urllib.request.urlopen")
def test_utils_dict_from_url_detailed(mock_urlopen):
    """Test dictionary handling from URL in more detail to cover line 68."""
    mock_response = mock.MagicMock()
    mock_response.headers = {}
    mock_response.read.return_value = b'{"key": "value", "nested": {"data": true}}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    results = list(stream_json_from_url("http://example.com/data.json"))

    assert len(results) == 1
    assert results[0]["key"] == "value"
    assert results[0]["nested"]["data"] is True


def test_query_edge_cases():
    """Test edge cases in the query module to increase coverage."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE instruments (
                instrument_key TEXT, exchange TEXT, instrument_type TEXT,
                name TEXT, segment TEXT, isin TEXT, option_type TEXT,
                expiry TEXT, trading_symbol TEXT, strike REAL
            )
        """
        )

        test_data = [
            (
                "TEST1",
                "NSE",
                "EQUITY",
                "Test Instrument",
                "EQ",
                "ISIN001",
                None,
                None,
                "TEST1",
                None,
            ),
            (
                "TEST2",
                "BSE",
                "EQUITY",
                "Test Instrument 2",
                "EQ",
                "ISIN002",
                None,
                None,
                "TEST2",
                None,
            ),
            (
                "TEST3",
                "NSE",
                "FUTURES",
                "Test Future",
                "FUT",
                "ISIN001",
                None,
                "2025-06-30",
                "TEST-FUT",
                None,
            ),
            (
                "TEST4",
                "NSE",
                "OPTIONS",
                "Test Option CE",
                "OPT",
                "ISIN001",
                "CE",
                "2025-06-30",
                "TEST-OPT",
                100,
            ),
            (
                "TEST5",
                "NSE",
                "OPTIONS",
                "Test Option PE",
                "OPT",
                "ISIN001",
                "PE",
                "2025-06-30",
                "TEST-OPT",
                100,
            ),
        ]

        cursor.executemany(
            "INSERT INTO instruments VALUES " "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            test_data,
        )
        conn.commit()
        conn.close()

        query = InstrumentQuery(db_path)

        results = query.get_option_chain("NONEXISTENT")
        assert len(results) == 0

        results = query.get_option_chain("ISIN001", expiry="2030-01-01")
        assert len(results) == 0

        result = query.get_by_trading_symbol("NONEXISTENT")
        assert result is None

        assert len(query.filter_by_exchange("UNKNOWN")) == 0
        assert len(query.filter_by_instrument_type("UNKNOWN")) == 0
        assert len(query.filter_by_segment("UNKNOWN")) == 0
        assert len(query.filter_by_isin("UNKNOWN")) == 0
        assert len(query.filter_by_option_type("UNKNOWN")) == 0
        assert len(query.search_by_name("NONEXISTENT")) == 0

        assert len(query.search_by_name("NONEXISTENT", case_sensitive=True)) == 0

        assert len(query.custom_query("exchange = ?", ("UNKNOWN",))) == 0

        pe_options = query.filter_by_option_type("PE")
        assert len(pe_options) == 1
        assert pe_options[0]["instrument_key"] == "TEST5"

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_query_module_all_branches():
    """Test all branches in the query module for 100% coverage."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE instruments (
                instrument_key TEXT, exchange TEXT, instrument_type TEXT,
                name TEXT, segment TEXT, isin TEXT, option_type TEXT,
                expiry TEXT, trading_symbol TEXT, strike REAL,
                lot_size INTEGER, tick_size REAL, exchange_token TEXT,
                short_name TEXT, freeze_quantity REAL, security_type TEXT,
                last_price REAL
            )
        """
        )

        test_data = [
            (
                "NSE_EQ_1",
                "NSE",
                "EQUITY",
                "Test NSE 1",
                "EQ",
                "ISIN001",
                None,
                None,
                "TST1",
                None,
                1,
                0.05,
                "ET1",
                "TST1",
                100.0,
                "NORMAL",
                100.0,
            ),
            (
                "BSE_EQ_1",
                "BSE",
                "EQUITY",
                "Test BSE 1",
                "EQ",
                "ISIN001",
                None,
                None,
                "TST1",
                None,
                1,
                0.05,
                "ET2",
                "TST1",
                100.0,
                "NORMAL",
                100.0,
            ),
            (
                "NSE_EQ_2",
                "NSE",
                "EQUITY",
                "Another Test",
                "EQ",
                "ISIN002",
                None,
                None,
                "TST2",
                None,
                1,
                0.05,
                "ET3",
                "TST2",
                100.0,
                "NORMAL",
                100.0,
            ),
            # Futures
            (
                "NSE_FUT_1",
                "NSE",
                "FUTURES",
                "Test Future",
                "FUT",
                "ISIN001",
                None,
                "2025-06-30",
                "TST1F",
                None,
                50,
                0.05,
                "ET4",
                "TST1F",
                500.0,
                "NORMAL",
                103.0,
            ),
            # Options - both CE and PE
            (
                "NSE_OPT_CE",
                "NSE",
                "OPTIONS",
                "Test CE Option",
                "OPT",
                "ISIN001",
                "CE",
                "2025-06-30",
                "TST1CE",
                100.0,
                50,
                0.05,
                "ET5",
                "TST1CE",
                500.0,
                "NORMAL",
                5.0,
            ),
            (
                "NSE_OPT_PE",
                "NSE",
                "OPTIONS",
                "Test PE Option",
                "OPT",
                "ISIN001",
                "PE",
                "2025-06-30",
                "TST1PE",
                100.0,
                50,
                0.05,
                "ET6",
                "TST1PE",
                500.0,
                "NORMAL",
                5.0,
            ),
            # Different expiry
            (
                "NSE_OPT_CE_2",
                "NSE",
                "OPTIONS",
                "Test CE Option 2",
                "OPT",
                "ISIN001",
                "CE",
                "2025-12-31",
                "TST1CE2",
                110.0,
                50,
                0.05,
                "ET7",
                "TST1CE2",
                500.0,
                "NORMAL",
                4.0,
            ),
        ]

        cursor.executemany(
            "INSERT INTO instruments VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            test_data,
        )
        conn.commit()
        conn.close()

        query = InstrumentQuery(db_path)

        result = query.get_by_instrument_key("NONEXISTENT")
        assert result is None

        nse_results = query.filter_by_exchange("NSE")
        assert len(nse_results) == 6
        unknown_exchange = query.filter_by_exchange("UNKNOWN")
        assert len(unknown_exchange) == 0

        equity_results = query.filter_by_instrument_type("EQUITY")
        assert len(equity_results) == 3
        unknown_type = query.filter_by_instrument_type("UNKNOWN")
        assert len(unknown_type) == 0

        eq_results = query.filter_by_segment("EQ")
        assert len(eq_results) == 3
        unknown_segment = query.filter_by_segment("UNKNOWN")
        assert len(unknown_segment) == 0

        isin_results = query.filter_by_isin("ISIN001")
        assert len(isin_results) == 6
        unknown_isin = query.filter_by_isin("UNKNOWN")
        assert len(unknown_isin) == 0

        ce_results = query.filter_by_option_type("CE")
        assert len(ce_results) == 2
        pe_results = query.filter_by_option_type("PE")
        assert len(pe_results) == 1
        unknown_option = query.filter_by_option_type("UNKNOWN")
        assert len(unknown_option) == 0

        name_results = query.search_by_name("Test")
        assert len(name_results) > 0
        case_sensitive = query.search_by_name("test", case_sensitive=True)
        assert len(case_sensitive) == 0
        unknown_name = query.search_by_name("NONEXISTENT")
        assert len(unknown_name) == 0

        symbol_result = query.get_by_trading_symbol("TST1")
        assert symbol_result is not None
        with_exchange = query.get_by_trading_symbol("TST1", exchange="NSE")
        assert with_exchange is not None
        wrong_exchange = query.get_by_trading_symbol("TST1", exchange="UNKNOWN")
        assert wrong_exchange is None
        unknown_symbol = query.get_by_trading_symbol("UNKNOWN")
        assert unknown_symbol is None

        chain_results = query.get_option_chain("ISIN001")
        assert len(chain_results) == 3
        with_expiry = query.get_option_chain("ISIN001", expiry="2025-06-30")
        assert len(with_expiry) == 2
        wrong_expiry = query.get_option_chain("ISIN001", expiry="2023-01-01")
        assert len(wrong_expiry) == 0
        unknown_option_chain = query.get_option_chain("UNKNOWN")
        assert len(unknown_option_chain) == 0

    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
