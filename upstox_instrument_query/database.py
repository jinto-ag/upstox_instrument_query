"""SQLite database handler for Upstox instrument data.

This module provides functionality to create and manage a SQLite database
for storing and querying Upstox instrument data.
"""

import re
import sqlite3
from typing import Optional

from .utils import stream_json, stream_json_from_url


class InstrumentDatabase:
    """
    SQLite database handler for Upstox instrument data.

    This class provides methods to initialize and manage a SQLite database
    that stores Upstox instrument data. It supports loading data from both
    local JSON files and remote URLs.
    """

    def __init__(self, db_path: str):
        """
        Initialize the database handler.

        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    def connect(self):
        """
        Connect to the SQLite database.

        Establishes a connection to the database and creates a cursor.
        """
        self.conn = sqlite3.connect(self.db_path)

        # Add REGEXP function support
        def regexp(expr, item):
            if item is None:
                return False
            reg = re.compile(expr)
            return reg.search(item) is not None

        if self.conn:
            self.conn.create_function("REGEXP", 2, regexp)
            self.cursor = self.conn.cursor()

    def close(self):
        """
        Close the database connection.

        Safely closes the connection if it exists.
        """
        if self.conn:
            self.conn.close()

    def initialize(self, json_source: str, is_url: bool = False):
        """
        Initialize the database from a JSON file or URL.

        Creates the necessary tables, loads data, and sets up indexes
        for optimal query performance.

        Args:
            json_source (str): Path to JSON file or URL
            is_url (bool, optional): Whether json_source is a URL. Defaults to False.
        """
        self.connect()
        self._create_table()
        if is_url:
            self._load_json_from_url(json_source)
        else:
            self._load_json(json_source)
        self._create_indexes()
        if self.conn:
            self.conn.commit()

    def _create_table(self):
        """
        Create the instruments table.

        Creates the main table structure for storing instrument data
        if it doesn't already exist.
        """
        if self.cursor:
            self.cursor.execute(
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

    def _load_json(self, json_path: str):
        """
        Load JSON data from a local file into the SQLite table.

        Processes the JSON data in a streaming fashion to handle large files.

        Args:
            json_path (str): Path to the local JSON file
        """
        if not self.cursor:
            return

        for instrument in stream_json(json_path):
            self.cursor.execute(
                """
                INSERT INTO instruments (
                    instrument_key, exchange, instrument_type, name, lot_size,
                    expiry, strike, tick_size, segment, exchange_token, trading_symbol,
                    short_name, isin, option_type, freeze_quantity, security_type, last_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    instrument.get("instrument_key"),
                    instrument.get("exchange"),
                    instrument.get("instrument_type"),
                    instrument.get("name"),
                    instrument.get("lot_size"),
                    instrument.get("expiry"),
                    instrument.get("strike"),
                    instrument.get("tick_size"),
                    instrument.get("segment"),
                    instrument.get("exchange_token"),
                    instrument.get("trading_symbol"),
                    instrument.get("short_name"),
                    instrument.get("isin"),
                    instrument.get("option_type"),
                    instrument.get("freeze_quantity"),
                    instrument.get("security_type"),
                    instrument.get("last_price"),
                ),
            )

    def _load_json_from_url(self, url: str):
        """
        Load JSON data from a URL into the SQLite table.

        Handles streaming of potentially gzipped JSON data from a remote URL.

        Args:
            url (str): URL to the JSON data (can be gzipped)
        """
        if not self.cursor:
            return

        for instrument in stream_json_from_url(url):
            self.cursor.execute(
                """
                INSERT INTO instruments (
                    instrument_key, exchange, instrument_type, name, lot_size,
                    expiry, strike, tick_size, segment, exchange_token, trading_symbol,
                    short_name, isin, option_type, freeze_quantity, security_type, last_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    instrument.get("instrument_key"),
                    instrument.get("exchange"),
                    instrument.get("instrument_type"),
                    instrument.get("name"),
                    instrument.get("lot_size"),
                    instrument.get("expiry"),
                    instrument.get("strike"),
                    instrument.get("tick_size"),
                    instrument.get("segment"),
                    instrument.get("exchange_token"),
                    instrument.get("trading_symbol"),
                    instrument.get("short_name"),
                    instrument.get("isin"),
                    instrument.get("option_type"),
                    instrument.get("freeze_quantity"),
                    instrument.get("security_type"),
                    instrument.get("last_price"),
                ),
            )

    def _create_indexes(self):
        """
        Create indexes on frequently queried fields.

        Adds database indexes to optimize query performance on commonly used fields.
        """
        if not self.cursor:
            return

        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_instrument_key ON instruments(instrument_key)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_exchange ON instruments(exchange)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_instrument_type ON instruments(instrument_type)"
        )
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON instruments(name)")
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_segment ON instruments(segment)"
        )
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_isin ON instruments(isin)")

    def update_instruments(self, json_source: str, is_url: bool = False):
        """
        Update the instruments in the database from a JSON file or URL.

        This is used to refresh instrument data without recreating the entire database.
        Existing instruments are deleted before new data is loaded.

        Args:
            json_source (str): Path to JSON file or URL
            is_url (bool, optional): Whether json_source is a URL. Defaults to False.
        """
        self.connect()
        # Delete existing instruments
        if self.cursor:
            self.cursor.execute("DELETE FROM instruments")
            # Load new data
            if is_url:
                self._load_json_from_url(json_source)
            else:
                self._load_json(json_source)
            if self.conn:
                self.conn.commit()
