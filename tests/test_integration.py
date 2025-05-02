"""Integration tests for the upstox_instrument_query package.

This module tests the complete workflow from database initialization to
querying, ensuring all components work together correctly.
"""

import os
import sqlite3
import tempfile
from unittest import mock

import pytest

from upstox_instrument_query.database import InstrumentDatabase
from upstox_instrument_query.query import InstrumentQuery


def test_end_to_end_flow(sample_json_path):
    """Test the complete workflow from initialization to querying."""
    # Create a temporary database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        # Initialize the database
        db = InstrumentDatabase(db_path)
        db.initialize(sample_json_path)
        db.close()

        # Verify database has been correctly initialized
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM instruments")
        count = cursor.fetchone()[0]
        assert count == 5  # We now have 5 instruments in our sample data
        conn.close()

        # Create a query interface
        query = InstrumentQuery(db_path)

        # Test various query methods
        instrument = query.get_by_instrument_key("NSE_EQ|INE001A01036")
        assert instrument is not None
        assert instrument["trading_symbol"] == "TESTCO1"
        assert instrument["isin"] == "INE001A01036"
        assert instrument["security_type"] == "NORMAL"

        nse_instruments = query.filter_by_exchange("NSE")
        assert len(nse_instruments) == 4

        equities = query.filter_by_instrument_type("EQUITY")
        assert len(equities) == 3

        # Test search by name
        company1 = query.search_by_name("TEST COMPANY 1")
        assert len(company1) == 3  # Equity, Futures, Options

        # Test by segment
        eq_segment = query.filter_by_segment("EQ")
        assert len(eq_segment) == 3

        # Test ISIN filter
        isin_results = query.filter_by_isin("INE001A01036")
        assert len(isin_results) == 3

        # Test options filter
        ce_options = query.filter_by_option_type("CE")
        assert len(ce_options) == 1

        # Test get by trading symbol
        symbol_result = query.get_by_trading_symbol("TESTCO1")
        assert symbol_result is not None
        assert symbol_result["instrument_key"] == "NSE_EQ|INE001A01036"

        # Test option chain
        option_chain = query.get_option_chain("INE001A01036", "2025-12-31")
        assert len(option_chain) == 1
        assert option_chain[0]["strike"] == 1100.0

        # Test custom query
        futures_2025 = query.custom_query(
            "instrument_type = ? AND expiry LIKE ?", ("FUTURES", "2025%")
        )
        assert len(futures_2025) == 1
        assert futures_2025[0]["trading_symbol"] == "TESTCO1-FUT-25DEC"

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


@mock.patch("upstox_instrument_query.database.stream_json_from_url")
def test_initialization_from_url(mock_stream_json):
    """Test initializing the database from a URL."""
    # Mock the URL streaming function
    mock_stream_json.return_value = [
        {
            "instrument_key": "NSE_EQ|INE001A01036",
            "exchange": "NSE",
            "instrument_type": "EQUITY",
            "name": "TEST COMPANY 1",
            "lot_size": 1,
            "expiry": None,
            "strike": None,
            "tick_size": 0.05,
            "segment": "EQ",
            "exchange_token": "123456",
            "trading_symbol": "TESTCO1",
            "short_name": "TESTCO1",
            "isin": "INE001A01036",
            "freeze_quantity": 100000.0,
            "security_type": "NORMAL",
            "last_price": 1000.0,
        }
    ]

    # Create a temporary database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        # Initialize the database from URL
        db = InstrumentDatabase(db_path)
        db.initialize("https://example.com/instruments.json", is_url=True)
        db.close()

        # Verify database was initialized
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM instruments")
        count = cursor.fetchone()[0]
        assert count == 1

        cursor.execute("SELECT trading_symbol, isin, security_type FROM instruments")
        row = cursor.fetchone()
        assert row[0] == "TESTCO1"
        assert row[1] == "INE001A01036"
        assert row[2] == "NORMAL"

        conn.close()

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


@mock.patch("upstox_instrument_query.database.stream_json_from_url")
def test_update_instruments_from_url(mock_stream_json):
    """Test updating instruments from a URL."""
    # Mock the URL streaming function
    mock_stream_json.return_value = [
        {
            "instrument_key": "NSE_EQ|INE001A01036",
            "exchange": "NSE",
            "instrument_type": "EQUITY",
            "name": "UPDATED COMPANY 1",
            "lot_size": 1,
            "expiry": None,
            "strike": None,
            "tick_size": 0.05,
            "segment": "EQ",
            "exchange_token": "123456",
            "trading_symbol": "TESTCO1",
            "short_name": "TESTCO1",
            "isin": "INE001A01036",
            "freeze_quantity": 100000.0,
            "security_type": "NORMAL",
            "last_price": 1000.0,
        }
    ]

    # Create a temporary database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        # Initialize the database with test data
        db = InstrumentDatabase(db_path)
        db.connect()
        db._create_table()
        db.cursor.execute(
            """
            INSERT INTO instruments (instrument_key, name)
            VALUES ('TEST_KEY', 'TEST INSTRUMENT')
            """
        )
        db.conn.commit()

        # Update instruments from URL
        db.update_instruments("https://example.com/instruments.json", is_url=True)

        # Verify database was updated
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM instruments")
        count = cursor.fetchone()[0]
        assert count == 1

        cursor.execute("SELECT name FROM instruments")
        name = cursor.fetchone()[0]
        assert name == "UPDATED COMPANY 1"

        conn.close()

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_query_caching(initialized_db):
    """Test that the query results are properly cached."""
    query = InstrumentQuery(initialized_db)

    # First call to get_by_instrument_key - will be cached
    result1 = query.get_by_instrument_key("NSE_EQ|INE001A01036")
    assert result1 is not None

    # First call to filter_by_exchange - will be cached
    nse_results = query.filter_by_exchange("NSE")
    assert len(nse_results) > 0

    # First call to other methods - will be cached
    eq_results = query.filter_by_segment("EQ")
    assert len(eq_results) > 0

    isin_results = query.filter_by_isin("INE001A01036")
    assert len(isin_results) > 0

    # Now drop the table
    conn = sqlite3.connect(initialized_db)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE instruments")
    conn.commit()
    conn.close()

    # Second call should use cache even though the table no longer exists
    result2 = query.get_by_instrument_key("NSE_EQ|INE001A01036")
    assert result2 is not None
    assert result2["instrument_key"] == "NSE_EQ|INE001A01036"

    # Test that cached results from other methods also work
    nse_results2 = query.filter_by_exchange("NSE")
    assert len(nse_results2) > 0
    assert nse_results == nse_results2  # Results should be identical

    eq_results2 = query.filter_by_segment("EQ")
    assert len(eq_results2) > 0

    isin_results2 = query.filter_by_isin("INE001A01036")
    assert len(isin_results2) > 0

    # Verify if we try a non-cached query, it will fail since the table is gone
    with pytest.raises(sqlite3.OperationalError):
        query.custom_query("exchange = ? AND name = ?", ("NSE", "NEW QUERY"))
