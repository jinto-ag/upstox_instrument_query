"""Tests for the query module.

This module tests the query functionality for filtering and retrieving
instrument data from the database.
"""


def test_query_init(initialized_db):
    """Test InstrumentQuery initialization."""
    from upstox_instrument_query.query import InstrumentQuery

    query = InstrumentQuery(initialized_db)
    assert query is not None
    assert query.db is not None
    assert query.db.db_path == initialized_db


def test_get_by_instrument_key(instrument_query):
    """Test getting an instrument by its key."""

    result = instrument_query.get_by_instrument_key("NSE_EQ|INE001A01036")
    assert result is not None
    assert result["instrument_key"] == "NSE_EQ|INE001A01036"
    assert result["name"] == "TEST COMPANY 1"
    assert result["exchange"] == "NSE"
    assert result["isin"] == "INE001A01036"
    assert result["security_type"] == "NORMAL"

    result = instrument_query.get_by_instrument_key("INVALID_KEY")
    assert result is None

    result = instrument_query.get_by_instrument_key("NSE_EQ|INE001A01036")
    assert result is not None
    assert result["instrument_key"] == "NSE_EQ|INE001A01036"


def test_filter_by_exchange(instrument_query):
    """Test filtering instruments by exchange."""

    nse_results = instrument_query.filter_by_exchange("NSE")
    assert len(nse_results) == 4

    bse_results = instrument_query.filter_by_exchange("BSE")
    assert len(bse_results) == 1

    unknown_results = instrument_query.filter_by_exchange("UNKNOWN")
    assert len(unknown_results) == 0


def test_filter_by_instrument_type(instrument_query):
    """Test filtering instruments by type."""

    equity_results = instrument_query.filter_by_instrument_type("EQUITY")
    assert len(equity_results) == 3

    futures_results = instrument_query.filter_by_instrument_type("FUTURES")
    assert len(futures_results) == 1

    options_results = instrument_query.filter_by_instrument_type("OPTIONS")
    assert len(options_results) == 1

    unknown_results = instrument_query.filter_by_instrument_type("UNKNOWN")
    assert len(unknown_results) == 0


def test_filter_by_segment(instrument_query):
    """Test filtering instruments by segment."""

    eq_results = instrument_query.filter_by_segment("EQ")
    assert len(eq_results) == 3

    fut_results = instrument_query.filter_by_segment("FUT")
    assert len(fut_results) == 1

    opt_results = instrument_query.filter_by_segment("OPT")
    assert len(opt_results) == 1

    unknown_results = instrument_query.filter_by_segment("UNKNOWN")
    assert len(unknown_results) == 0


def test_filter_by_isin(instrument_query):
    """Test filtering instruments by ISIN."""

    isin1_results = instrument_query.filter_by_isin("INE001A01036")
    assert len(isin1_results) == 3

    isin2_results = instrument_query.filter_by_isin("INE002A01018")
    assert len(isin2_results) == 2

    unknown_results = instrument_query.filter_by_isin("INVALID")
    assert len(unknown_results) == 0


def test_filter_by_option_type(instrument_query):
    """Test filtering instruments by option type."""

    ce_results = instrument_query.filter_by_option_type("CE")
    assert len(ce_results) == 1
    assert ce_results[0]["strike"] == 1100.0

    pe_results = instrument_query.filter_by_option_type("PE")
    assert len(pe_results) == 0


def test_search_by_name(instrument_query):
    """Test searching instruments by name."""

    results = instrument_query.search_by_name("company 1")
    assert len(results) == 3

    results = instrument_query.search_by_name("COMPANY 1", case_sensitive=True)
    assert len(results) == 3

    results = instrument_query.search_by_name("^TEST.*1$")
    assert len(results) == 1
    assert results[0]["name"] == "TEST COMPANY 1"

    results = instrument_query.search_by_name("NONEXISTENT")
    assert len(results) == 0


def test_custom_query(instrument_query):
    """Test custom query with WHERE clause."""

    results = instrument_query.custom_query(
        "exchange = ? AND instrument_type = ?", ("NSE", "EQUITY")
    )
    assert len(results) == 2

    results = instrument_query.custom_query("name LIKE ?", ("TEST COMPANY%",))
    assert len(results) == 5

    results = instrument_query.custom_query(
        "exchange = ? AND instrument_type = ? AND lot_size > ?",
        ("NSE", "FUTURES", 50),
    )
    assert len(results) == 1
    assert results[0]["trading_symbol"] == "TESTCO1-FUT-25DEC"

    results = instrument_query.custom_query("security_type = ?", ("OPTIONS",))
    assert len(results) == 1
    assert results[0]["instrument_type"] == "OPTIONS"

    results = instrument_query.custom_query(
        "exchange = ? AND instrument_type = ?", ("BSE", "FUTURES")
    )
    assert len(results) == 0


def test_get_by_trading_symbol(instrument_query):
    """Test getting instrument by trading symbol."""

    result = instrument_query.get_by_trading_symbol("TESTCO1")
    assert result is not None
    assert result["instrument_key"] == "NSE_EQ|INE001A01036"

    result = instrument_query.get_by_trading_symbol("TESTCO2", exchange="NSE")
    assert result is not None
    assert result["instrument_key"] == "NSE_EQ|INE002A01018"

    result = instrument_query.get_by_trading_symbol("TESTCO1", exchange="BSE")
    assert result is None

    result = instrument_query.get_by_trading_symbol("NONEXISTENT")
    assert result is None


def test_get_option_chain(instrument_query):
    """Test getting option chain for underlying security."""

    results = instrument_query.get_option_chain("INE001A01036")
    assert len(results) == 1
    assert results[0]["option_type"] == "CE"
    assert results[0]["strike"] == 1100.0

    results = instrument_query.get_option_chain("INE001A01036", expiry="2025-12-31")
    assert len(results) == 1

    results = instrument_query.get_option_chain("INE001A01036", expiry="2024-12-31")
    assert len(results) == 0

    results = instrument_query.get_option_chain("INVALID")
    assert len(results) == 0
