"""Constants and default values for Upstox Instrument Query.

This module contains default configurations, constants, and enums
to maintain consistency across the package.
"""

import os
import tempfile
from enum import Enum
from pathlib import Path

DEFAULT_INSTRUMENTS_URL = (
    "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"
)


DEFAULT_DB_PATH = os.path.join(str(Path.home()), ".upstox_instruments.db")


TEMP_DB_PATH = os.path.join(tempfile.gettempdir(), "upstox_instruments_temp.db")


class CommandType(Enum):
    """Enum for command types."""

    INIT = "init"
    UPDATE = "update"
    QUERY = "query"
    INTERACTIVE = "interactive"


class InstrumentType(Enum):
    """Enum for instrument types."""

    EQUITY = "EQUITY"
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"
    INDEX = "INDEX"
    CURRENCY = "CURRENCY"
    COMMODITY = "COMMODITY"


class Exchange(Enum):
    """Enum for exchanges."""

    NSE = "NSE"
    BSE = "BSE"
    MCX = "MCX"
    NCDEX = "NCDEX"
    BCD = "BCD"


class OptionType(Enum):
    """Enum for option types."""

    CALL = "CE"
    PUT = "PE"
