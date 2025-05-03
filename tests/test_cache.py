"""Tests for query cache clearing in the upstox_instrument_query package."""

import os
import tempfile

import pytest

from upstox_instrument_query.database import InstrumentDatabase
from upstox_instrument_query.query import InstrumentQuery


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, temp_file = tempfile.mkstemp()
    os.close(fd)

    db = InstrumentDatabase(temp_file)
    db.connect()

    db._create_table()
    if db.cursor and db.conn:
        db.cursor.execute(
            """
            INSERT INTO instruments
            (instrument_key, exchange, instrument_type, name, trading_symbol, isin)
            VALUES
            (?, ?, ?, ?, ?, ?)
            """,
            (
                "NSE_EQ|INE123456789",
                "NSE",
                "EQ",
                "Test Stock",
                "TESTSTOCK",
                "INE123456789",
            ),
        )

        db.conn.commit()

    yield temp_file

    os.unlink(temp_file)


def test_clear_cache(temp_db):
    """Test that clear_cache properly clears all cached query results."""

    query = InstrumentQuery(temp_db)

    _ = query.get_by_instrument_key("NSE_EQ|INE123456789")
    _ = query.filter_by_exchange("NSE")
    _ = query.filter_by_instrument_type("EQ")
    _ = query.filter_by_isin("INE123456789")

    assert query.get_by_instrument_key.cache_info().currsize > 0
    assert query.filter_by_exchange.cache_info().currsize > 0
    assert query.filter_by_instrument_type.cache_info().currsize > 0
    assert query.filter_by_isin.cache_info().currsize > 0

    query.clear_cache()

    assert query.get_by_instrument_key.cache_info().currsize == 0
    assert query.filter_by_exchange.cache_info().currsize == 0
    assert query.filter_by_instrument_type.cache_info().currsize == 0
    assert query.filter_by_isin.cache_info().currsize == 0
