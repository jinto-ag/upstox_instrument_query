"""Tests for the database module.

This module tests the SQLite database functionality for storing and retrieving
instrument data.
"""

import sqlite3  # Removed unused 'os' import

import pytest

from upstox_instrument_query.database import InstrumentDatabase


def test_database_init(temp_db_path):
    """Test database initialization."""
    db = InstrumentDatabase(temp_db_path)
    assert db.db_path == temp_db_path
    assert db.conn is None
    assert db.cursor is None


def test_database_connect(instrument_db):
    """Test database connection establishment."""
    instrument_db.connect()
    assert instrument_db.conn is not None
    assert instrument_db.cursor is not None
    assert isinstance(instrument_db.conn, sqlite3.Connection)
    assert isinstance(instrument_db.cursor, sqlite3.Cursor)


def test_database_close(instrument_db):
    """Test database connection closure."""
    instrument_db.connect()
    assert instrument_db.conn is not None

    instrument_db.close()
    # SQLite connections are automatically closed when the connection object is garbage collected
    # We can't directly test if the connection is closed, but we can check if operations fail
    with pytest.raises(Exception):
        instrument_db.cursor.execute("SELECT 1")


def test_close_without_connection():
    """Test closing database without an active connection."""
    db = InstrumentDatabase(":memory:")
    # No connection is established
    db.close()  # Should not raise any exceptions


def test_create_table(instrument_db):
    """Test table creation."""
    instrument_db.connect()
    instrument_db._create_table()

    # Verify table exists
    instrument_db.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='instruments'"
    )
    assert instrument_db.cursor.fetchone() is not None

    # Verify all necessary columns exist
    instrument_db.cursor.execute("PRAGMA table_info(instruments)")
    columns = [row[1] for row in instrument_db.cursor.fetchall()]

    # Check that all expected columns are present
    expected_columns = [
        "instrument_key",
        "exchange",
        "instrument_type",
        "name",
        "lot_size",
        "expiry",
        "strike",
        "tick_size",
        "segment",
        "exchange_token",
        "trading_symbol",
        "short_name",
        "isin",
        "option_type",
        "freeze_quantity",
        "security_type",
        "last_price",
    ]

    for column in expected_columns:
        assert column in columns


def test_create_indexes(instrument_db):
    """Test index creation."""
    instrument_db.connect()
    instrument_db._create_table()
    instrument_db._create_indexes()

    # Verify indexes exist
    instrument_db.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='instruments'"
    )
    indexes = [row[0] for row in instrument_db.cursor.fetchall()]

    expected_indexes = [
        "idx_instrument_key",
        "idx_exchange",
        "idx_instrument_type",
        "idx_name",
        "idx_segment",
        "idx_isin",
    ]

    for index in expected_indexes:
        assert index in indexes


def test_load_json(temp_db_path, sample_json_path):
    """Test loading data from a JSON file."""
    db = InstrumentDatabase(temp_db_path)
    db.connect()
    db._create_table()
    db._load_json(sample_json_path)

    # Verify data was loaded
    db.cursor.execute("SELECT COUNT(*) FROM instruments")
    count = db.cursor.fetchone()[0]
    assert count == 5  # We now have 5 instruments in our sample data

    # Verify specific data including new fields
    db.cursor.execute(
        "SELECT * FROM instruments WHERE instrument_key = ?", ("NSE_EQ|INE001A01036",)
    )
    result = db.cursor.fetchone()
    assert result is not None

    # Check that columns match expected values
    db.cursor.execute("PRAGMA table_info(instruments)")
    columns = [row[1] for row in db.cursor.fetchall()]
    result_dict = dict(zip(columns, result))

    assert result_dict["exchange"] == "NSE"
    assert result_dict["instrument_type"] == "EQUITY"
    assert result_dict["name"] == "TEST COMPANY 1"
    assert result_dict["isin"] == "INE001A01036"
    assert result_dict["short_name"] == "TESTCO1"
    assert result_dict["security_type"] == "NORMAL"

    # Test option instrument
    db.cursor.execute("SELECT * FROM instruments WHERE option_type = ?", ("CE",))
    result = db.cursor.fetchone()
    assert result is not None
    result_dict = dict(zip(columns, result))
    assert result_dict["instrument_type"] == "OPTIONS"
    assert result_dict["strike"] == 1100.0


def test_initialize(temp_db_path, sample_json_path):
    """Test complete database initialization."""
    db = InstrumentDatabase(temp_db_path)
    db.initialize(sample_json_path)

    # Connect to the database to verify
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    # Check if all expected tables and indexes exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'index')")
    objects = [row[0] for row in cursor.fetchall()]

    expected_objects = [
        "instruments",
        "idx_instrument_key",
        "idx_exchange",
        "idx_instrument_type",
        "idx_name",
        "idx_segment",
        "idx_isin",
    ]

    for obj in expected_objects:
        assert obj in objects

    # Check data
    cursor.execute("SELECT COUNT(*) FROM instruments")
    count = cursor.fetchone()[0]
    assert count == 5

    conn.close()


def test_update_instruments(temp_db_path, sample_json_path):
    """Test the update_instruments method."""
    # Initialize an empty database
    db = InstrumentDatabase(temp_db_path)
    db.connect()
    db._create_table()
    db.cursor.execute(
        """
        INSERT INTO instruments (instrument_key, name)
        VALUES ('TEST_KEY', 'TEST INSTRUMENT')
        """
    )
    db.conn.commit()

    # Verify the test record exists
    db.cursor.execute("SELECT COUNT(*) FROM instruments")
    count = db.cursor.fetchone()[0]
    assert count == 1

    # Update instruments
    db.update_instruments(sample_json_path)

    # Verify old data is gone and new data is loaded
    db.cursor.execute("SELECT COUNT(*) FROM instruments")
    count = db.cursor.fetchone()[0]
    assert count == 5

    # Verify the test record is gone
    db.cursor.execute(
        "SELECT COUNT(*) FROM instruments WHERE instrument_key = ?", ("TEST_KEY",)
    )
    count = db.cursor.fetchone()[0]
    assert count == 0

    # Verify specific data was loaded
    db.cursor.execute("SELECT COUNT(*) FROM instruments WHERE option_type = ?", ("CE",))
    count = db.cursor.fetchone()[0]
    assert count == 1


def test_database_regexp_function():
    """Test the REGEXP function in SQLite."""
    db = InstrumentDatabase(":memory:")
    db.connect()
    db._create_table()

    # Insert sample data
    db.cursor.execute(
        """
        INSERT INTO instruments (instrument_key, name)
        VALUES (?, ?)
        """,
        ("TEST_KEY", "TEST INSTRUMENT"),
    )
    db.conn.commit()

    # Test REGEXP with matching pattern
    db.cursor.execute("SELECT * FROM instruments WHERE name REGEXP ?", ("^TEST.*",))
    result = db.cursor.fetchone()
    assert result is not None

    # Test REGEXP with non-matching pattern
    db.cursor.execute("SELECT * FROM instruments WHERE name REGEXP ?", ("^NOMATCH.*",))
    result = db.cursor.fetchone()
    assert result is None

    # Test REGEXP with NULL value
    db.cursor.execute(
        """
        INSERT INTO instruments (instrument_key, name)
        VALUES (?, ?)
        """,
        ("NULL_TEST", None),
    )
    db.conn.commit()

    db.cursor.execute("SELECT * FROM instruments WHERE name REGEXP ?", (".*",))
    results = db.cursor.fetchall()
    assert len(results) == 1  # Only the non-NULL value should match
