"""Tests for the constants module.

This module tests the constants and default values provided by the constants module.
"""

import os
from pathlib import Path

from upstox_instrument_query.constants import (
    DEFAULT_DB_PATH,
    DEFAULT_INSTRUMENTS_URL,
    CommandType,
    Exchange,
    InstrumentType,
    OptionType,
)


def test_default_values():
    """Test that default values are properly defined."""

    assert (
        DEFAULT_INSTRUMENTS_URL
        == "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"
    )

    expected_db_path = os.path.join(str(Path.home()), ".upstox_instruments.db")
    assert DEFAULT_DB_PATH == expected_db_path


def test_command_type_enum():
    """Test that CommandType enum is correctly defined."""
    assert CommandType.INIT.value == "init"
    assert CommandType.UPDATE.value == "update"
    assert CommandType.QUERY.value == "query"
    assert CommandType.INTERACTIVE.value == "interactive"
    assert "init" == CommandType.INIT.value
    assert "update" == CommandType.UPDATE.value
    assert "query" == CommandType.QUERY.value
    assert "interactive" == CommandType.INTERACTIVE.value


def test_instrument_type_enum():
    """Test that InstrumentType enum is correctly defined."""
    assert InstrumentType.EQUITY.value == "EQUITY"
    assert InstrumentType.FUTURES.value == "FUTURES"
    assert InstrumentType.OPTIONS.value == "OPTIONS"
    assert InstrumentType.INDEX.value == "INDEX"
    assert InstrumentType.CURRENCY.value == "CURRENCY"
    assert InstrumentType.COMMODITY.value == "COMMODITY"


def test_exchange_enum():
    """Test that Exchange enum is correctly defined."""
    assert Exchange.NSE.value == "NSE"
    assert Exchange.BSE.value == "BSE"
    assert Exchange.MCX.value == "MCX"
    assert Exchange.NCDEX.value == "NCDEX"
    assert Exchange.BCD.value == "BCD"


def test_option_type_enum():
    """Test that OptionType enum is correctly defined."""
    assert OptionType.CALL.value == "CE"
    assert OptionType.PUT.value == "PE"
