"""Tests for query edge cases.

This module tests edge cases and error handling
in the InstrumentQuery class.
"""

import os
import sqlite3
import tempfile

import pytest

from upstox_instrument_query.query import InstrumentQuery


class TestQueryEdgeCases:
    """Tests specifically targeting edge cases in the query module."""

    @pytest.fixture
    def empty_query(self):
        """Create a query object with empty database."""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        # Create the database structure but don't add any data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE instruments (
                instrument_key TEXT PRIMARY KEY,
                exchange TEXT,
                instrument_type TEXT,
                name TEXT,
                segment TEXT,
                isin TEXT,
                option_type TEXT,
                expiry TEXT,
                trading_symbol TEXT,
                strike REAL,
                lot_size INTEGER,
                tick_size REAL
            )
        """
        )
        conn.commit()
        conn.close()

        query = InstrumentQuery(db_path)

        yield query

        # Clean up
        query.db.close()
        os.unlink(db_path)

    @pytest.fixture
    def minimal_query(self):
        """Create a query object with minimal test data."""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        # Set up database with test data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE instruments (
                instrument_key TEXT PRIMARY KEY,
                exchange TEXT,
                instrument_type TEXT,
                name TEXT,
                segment TEXT,
                isin TEXT,
                option_type TEXT,
                expiry TEXT,
                trading_symbol TEXT,
                strike REAL,
                lot_size INTEGER,
                tick_size REAL
            )
        """
        )

        test_data = [
            (
                "NSE_EQ_1",
                "NSE",
                "EQUITY",
                "Test Stock 1",
                "EQ",
                "ISIN001",
                None,
                None,
                "STOCK1",
                None,
                1,
                0.05,
            ),
            (
                "NSE_OPT_CE",
                "NSE",
                "OPTIONS",
                "Test Call Option",
                "OPT",
                "ISIN001",
                "CE",
                "2023-12-31",
                "OPT_CE",
                100.0,
                50,
                0.05,
            ),
            (
                "NSE_OPT_PE",
                "NSE",
                "OPTIONS",
                "Test Put Option",
                "OPT",
                "ISIN001",
                "PE",
                "2023-12-31",
                "OPT_PE",
                100.0,
                50,
                0.05,
            ),
        ]

        cursor.executemany(
            "INSERT INTO instruments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            test_data,
        )
        conn.commit()
        conn.close()

        query = InstrumentQuery(db_path)

        yield query

        # Clean up
        query.db.close()
        os.unlink(db_path)

    def test_get_by_instrument_key_nonexistent(self, minimal_query):
        """Test getting a nonexistent instrument key."""
        result = minimal_query.get_by_instrument_key("NONEXISTENT")
        assert result is None

    def test_filter_by_exchange_empty_results(self, minimal_query):
        """Test filtering by exchange with no matching results."""
        results = minimal_query.filter_by_exchange("NONEXISTENT")
        assert len(results) == 0

    def test_filter_by_instrument_type_empty_results(self, minimal_query):
        """Test filtering by instrument type with no matching results."""
        results = minimal_query.filter_by_instrument_type("NONEXISTENT")
        assert len(results) == 0

    def test_filter_by_segment_empty_results(self, minimal_query):
        """Test filtering by segment with no matching results."""
        results = minimal_query.filter_by_segment("NONEXISTENT")
        assert len(results) == 0

    def test_filter_by_isin_empty_results(self, minimal_query):
        """Test filtering by ISIN with no matching results."""
        results = minimal_query.filter_by_isin("NONEXISTENT")
        assert len(results) == 0

    def test_filter_by_option_type_empty_results(self, minimal_query):
        """Test filtering by option type with no matching results."""
        results = minimal_query.filter_by_option_type("NONEXISTENT")
        assert len(results) == 0

    def test_search_by_name_empty_results(self, minimal_query):
        """Test searching by name with no matching results."""
        results = minimal_query.search_by_name("NONEXISTENT")
        assert len(results) == 0

    def test_search_by_name_case_sensitive(self, minimal_query):
        """Test searching by name with case sensitivity."""
        results = minimal_query.search_by_name("test", case_sensitive=True)
        # Should match zero, as our test data has capital 'T'
        assert len(results) == 0

    def test_get_by_trading_symbol_nonexistent(self, minimal_query):
        """Test getting a nonexistent trading symbol."""
        result = minimal_query.get_by_trading_symbol("NONEXISTENT")
        assert result is None

    def test_get_by_trading_symbol_wrong_exchange(self, minimal_query):
        """Test getting a trading symbol with the wrong exchange."""
        result = minimal_query.get_by_trading_symbol("STOCK1", exchange="BSE")
        assert result is None

    def test_get_option_chain_nonexistent(self, minimal_query):
        """Test getting an option chain for a nonexistent ISIN."""
        results = minimal_query.get_option_chain("NONEXISTENT")
        assert len(results) == 0

    def test_get_option_chain_nonexistent_expiry(self, minimal_query):
        """Test getting an option chain with a nonexistent expiry date."""
        results = minimal_query.get_option_chain("ISIN001", expiry="2999-12-31")
        assert len(results) == 0

    def test_empty_database(self, empty_query):
        """Test querying with an empty database structure."""
        # This should test many of the empty result paths
        assert empty_query.get_by_instrument_key("ANY") is None
        assert len(empty_query.filter_by_exchange("ANY")) == 0
        assert len(empty_query.filter_by_instrument_type("ANY")) == 0
        assert len(empty_query.filter_by_segment("ANY")) == 0
        assert len(empty_query.filter_by_isin("ANY")) == 0
        assert len(empty_query.filter_by_option_type("ANY")) == 0
        assert len(empty_query.search_by_name("ANY")) == 0
        assert empty_query.get_by_trading_symbol("ANY") is None
        assert len(empty_query.get_option_chain("ANY")) == 0
