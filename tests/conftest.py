import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from upstox_instrument_query.database import InstrumentDatabase
from upstox_instrument_query.query import InstrumentQuery


@pytest.fixture(scope="session")
def test_data_dir():
    """Return path to the test data directory."""
    return os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture
def sample_json_path(test_data_dir):
    """Return path to the sample instruments JSON file."""
    return os.path.join(test_data_dir, "sample_instruments.json")


@pytest.fixture
def temp_db_path():
    """Create a temporary database file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup after test
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def initialized_db(temp_db_path, sample_json_path):
    """Initialize a database with sample data and return the path."""
    db = InstrumentDatabase(temp_db_path)
    db.initialize(sample_json_path)
    db.close()
    return temp_db_path


@pytest.fixture
def instrument_query(initialized_db):
    """Return an initialized InstrumentQuery instance."""
    query = InstrumentQuery(initialized_db)
    yield query
    # Clean up
    query.db.close()


@pytest.fixture
def instrument_db(temp_db_path):
    """Return an InstrumentDatabase instance."""
    db = InstrumentDatabase(temp_db_path)
    yield db
    # Clean up
    db.close()


@pytest.fixture
def sqlite_regexp():
    """Add REGEXP function to SQLite for testing."""

    def _regexp(expr, item):
        import re

        if item is None:
            return False
        reg = re.compile(expr)
        return reg.search(item) is not None

    conn = sqlite3.connect(":memory:")
    conn.create_function("REGEXP", 2, _regexp)
    yield conn
    conn.close()
