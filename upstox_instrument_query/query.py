from functools import lru_cache

from .database import InstrumentDatabase


class InstrumentQuery:
    """
    Query interface for the Upstox instrument database.

    This class provides optimized methods to query and filter Upstox instruments
    from a SQLite database. It uses caching for frequently accessed queries to
    improve performance.
    """

    def __init__(self, db_path: str):
        """
        Initialize the query interface with a database path.

        Args:
            db_path (str): Path to the SQLite database file containing instrument data
        """
        self.db = InstrumentDatabase(db_path)
        self.db.connect()

    def __del__(self):
        """Close the database connection when the object is destroyed."""
        self.db.close()

    @lru_cache(maxsize=1000)
    def get_by_instrument_key(self, instrument_key: str) -> dict:
        """
        Get an instrument by its instrument_key.

        Args:
            instrument_key (str): The unique instrument key (e.g., 'NSE_EQ|INE002A01018')

        Returns:
            dict: Instrument details as a dictionary or None if not found
        """
        self.db.cursor.execute(
            "SELECT * FROM instruments WHERE instrument_key = ?", (instrument_key,)
        )
        result = self.db.cursor.fetchone()
        if result:
            columns = [col[0] for col in self.db.cursor.description]
            return dict(zip(columns, result))
        return None

    @lru_cache(maxsize=1000)
    def filter_by_exchange(self, exchange: str) -> list:
        """
        Get all instruments for a given exchange.

        Args:
            exchange (str): Exchange code (e.g., 'NSE', 'BSE')

        Returns:
            list: List of instrument dictionaries matching the exchange
        """
        self.db.cursor.execute(
            "SELECT * FROM instruments WHERE exchange = ?", (exchange,)
        )
        columns = [col[0] for col in self.db.cursor.description]
        return [dict(zip(columns, row)) for row in self.db.cursor.fetchall()]

    @lru_cache(maxsize=1000)
    def filter_by_instrument_type(self, instrument_type: str) -> list:
        """
        Get all instruments of a given type.

        Args:
            instrument_type (str): Type of instrument (e.g., 'EQUITY', 'FUTURES')

        Returns:
            list: List of instrument dictionaries matching the instrument type
        """
        self.db.cursor.execute(
            "SELECT * FROM instruments WHERE instrument_type = ?", (instrument_type,)
        )
        columns = [col[0] for col in self.db.cursor.description]
        return [dict(zip(columns, row)) for row in self.db.cursor.fetchall()]

    @lru_cache(maxsize=1000)
    def filter_by_segment(self, segment: str) -> list:
        """
        Get all instruments for a given segment.

        Args:
            segment (str): Segment code (e.g., 'NSE_EQ', 'NSE_FO')

        Returns:
            list: List of instrument dictionaries matching the segment
        """
        self.db.cursor.execute(
            "SELECT * FROM instruments WHERE segment = ?", (segment,)
        )
        columns = [col[0] for col in self.db.cursor.description]
        return [dict(zip(columns, row)) for row in self.db.cursor.fetchall()]

    @lru_cache(maxsize=1000)
    def filter_by_isin(self, isin: str) -> list:
        """
        Get all instruments for a given ISIN.

        Args:
            isin (str): International Securities Identification Number

        Returns:
            list: List of instrument dictionaries matching the ISIN
        """
        self.db.cursor.execute("SELECT * FROM instruments WHERE isin = ?", (isin,))
        columns = [col[0] for col in self.db.cursor.description]
        return [dict(zip(columns, row)) for row in self.db.cursor.fetchall()]

    @lru_cache(maxsize=500)
    def filter_by_option_type(self, option_type: str) -> list:
        """
        Get all option instruments of a given option type.

        Args:
            option_type (str): Option type ('CE' for Call, 'PE' for Put)

        Returns:
            list: List of option instrument dictionaries matching the option type
        """
        self.db.cursor.execute(
            "SELECT * FROM instruments WHERE option_type = ?", (option_type,)
        )
        columns = [col[0] for col in self.db.cursor.description]
        return [dict(zip(columns, row)) for row in self.db.cursor.fetchall()]

    def search_by_name(self, name_pattern: str, case_sensitive: bool = False) -> list:
        """
        Search instruments by name using a regex pattern.

        Args:
            name_pattern (str): Regular expression pattern to match against instrument names
            case_sensitive (bool, optional): Whether the search should be case-sensitive. Defaults to False.

        Returns:
            list: List of instrument dictionaries matching the name pattern
        """
        query = "SELECT * FROM instruments WHERE name REGEXP ?"
        if not case_sensitive:
            name_pattern = f"(?i){name_pattern}"
        self.db.cursor.execute(query, (name_pattern,))
        columns = [col[0] for col in self.db.cursor.description]
        return [dict(zip(columns, row)) for row in self.db.cursor.fetchall()]

    def custom_query(self, where_clause: str, params: tuple = ()) -> list:
        """
        Execute a custom SQL query with a WHERE clause.

        Args:
            where_clause (str): SQL WHERE clause (without the 'WHERE' keyword)
            params (tuple, optional): Parameter values for the query placeholders. Defaults to ().

        Returns:
            list: List of instrument dictionaries matching the custom query

        Example:
            query.custom_query("instrument_type = ? AND expiry > ?", ("FUTURES", "2023-12-31"))
        """
        query = f"SELECT * FROM instruments WHERE {where_clause}"
        self.db.cursor.execute(query, params)
        columns = [col[0] for col in self.db.cursor.description]
        return [dict(zip(columns, row)) for row in self.db.cursor.fetchall()]

    @lru_cache(maxsize=1000)
    def get_by_trading_symbol(self, trading_symbol: str, exchange: str = None) -> dict:
        """
        Get an instrument by its trading symbol, optionally filtering by exchange.

        Args:
            trading_symbol (str): The trading symbol to search for
            exchange (str, optional): Exchange to filter by. Defaults to None.

        Returns:
            dict: Instrument details as a dictionary or None if not found
        """
        if exchange:
            self.db.cursor.execute(
                "SELECT * FROM instruments WHERE trading_symbol = ? AND exchange = ?",
                (trading_symbol, exchange),
            )
        else:
            self.db.cursor.execute(
                "SELECT * FROM instruments WHERE trading_symbol = ?", (trading_symbol,)
            )
        result = self.db.cursor.fetchone()
        if result:
            columns = [col[0] for col in self.db.cursor.description]
            return dict(zip(columns, result))
        return None

    def get_option_chain(self, underlying_isin: str, expiry: str = None) -> list:
        """
        Get the option chain for a specific underlying security by ISIN.

        Args:
            underlying_isin (str): ISIN of the underlying security
            expiry (str, optional): Filter by expiry date (format: 'YYYY-MM-DD'). Defaults to None.

        Returns:
            list: List of option instruments for the specified underlying
        """
        if expiry:
            return self.custom_query(
                "isin = ? AND instrument_type = 'OPTIONS' AND expiry = ?",
                (underlying_isin, expiry),
            )
        else:
            return self.custom_query(
                "isin = ? AND instrument_type = 'OPTIONS'", (underlying_isin,)
            )
