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
    # Test existing instrument
    result = instrument_query.get_by_instrument_key("NSE_EQ|INE001A01036")
    assert result is not None
    assert result["instrument_key"] == "NSE_EQ|INE001A01036"
    assert result["name"] == "TEST COMPANY 1"
    assert result["exchange"] == "NSE"
    assert result["isin"] == "INE001A01036"
    assert result["security_type"] == "NORMAL"

    # Test non-existent instrument
    result = instrument_query.get_by_instrument_key("INVALID_KEY")
    assert result is None

    # Test caching - call the same query again
    result = instrument_query.get_by_instrument_key("NSE_EQ|INE001A01036")
    assert result is not None
    assert result["instrument_key"] == "NSE_EQ|INE001A01036"


def test_filter_by_exchange(instrument_query):
    """Test filtering instruments by exchange."""
    # Test NSE instruments
    nse_results = instrument_query.filter_by_exchange("NSE")
    assert len(nse_results) == 4  # 2 equity, 1 futures, 1 options

    # Test BSE instruments
    bse_results = instrument_query.filter_by_exchange("BSE")
    assert len(bse_results) == 1

    # Test non-existent exchange
    unknown_results = instrument_query.filter_by_exchange("UNKNOWN")
    assert len(unknown_results) == 0


def test_filter_by_instrument_type(instrument_query):
    """Test filtering instruments by type."""
    # Test EQUITY instruments
    equity_results = instrument_query.filter_by_instrument_type("EQUITY")
    assert len(equity_results) == 3  # 2 NSE and 1 BSE

    # Test FUTURES instruments
    futures_results = instrument_query.filter_by_instrument_type("FUTURES")
    assert len(futures_results) == 1

    # Test OPTIONS instruments
    options_results = instrument_query.filter_by_instrument_type("OPTIONS")
    assert len(options_results) == 1

    # Test non-existent type
    unknown_results = instrument_query.filter_by_instrument_type("UNKNOWN")
    assert len(unknown_results) == 0


def test_filter_by_segment(instrument_query):
    """Test filtering instruments by segment."""
    # Test EQ segment
    eq_results = instrument_query.filter_by_segment("EQ")
    assert len(eq_results) == 3

    # Test FUT segment
    fut_results = instrument_query.filter_by_segment("FUT")
    assert len(fut_results) == 1

    # Test OPT segment
    opt_results = instrument_query.filter_by_segment("OPT")
    assert len(opt_results) == 1

    # Test non-existent segment
    unknown_results = instrument_query.filter_by_segment("UNKNOWN")
    assert len(unknown_results) == 0


def test_filter_by_isin(instrument_query):
    """Test filtering instruments by ISIN."""
    # Test first ISIN
    isin1_results = instrument_query.filter_by_isin("INE001A01036")
    assert len(isin1_results) == 3  # Equity, futures, options

    # Test second ISIN
    isin2_results = instrument_query.filter_by_isin("INE002A01018")
    assert len(isin2_results) == 2  # NSE and BSE

    # Test non-existent ISIN
    unknown_results = instrument_query.filter_by_isin("INVALID")
    assert len(unknown_results) == 0


def test_filter_by_option_type(instrument_query):
    """Test filtering instruments by option type."""
    # Test CE options
    ce_results = instrument_query.filter_by_option_type("CE")
    assert len(ce_results) == 1
    assert ce_results[0]["strike"] == 1100.0

    # Test PE options (none in our sample)
    pe_results = instrument_query.filter_by_option_type("PE")
    assert len(pe_results) == 0


def test_search_by_name(instrument_query):
    """Test searching instruments by name."""
    # Test case insensitive search
    results = instrument_query.search_by_name("company 1")
    assert len(results) == 3  # 1 equity, 1 futures, 1 options

    # Test case sensitive search
    results = instrument_query.search_by_name("COMPANY 1", case_sensitive=True)
    assert len(results) == 3

    # Test with regex pattern
    results = instrument_query.search_by_name("^TEST.*1$")
    assert len(results) == 1
    assert results[0]["name"] == "TEST COMPANY 1"

    # Test non-matching pattern
    results = instrument_query.search_by_name("NONEXISTENT")
    assert len(results) == 0


def test_custom_query(instrument_query):
    """Test custom query with WHERE clause."""
    # Test simple query
    results = instrument_query.custom_query(
        "exchange = ? AND instrument_type = ?", ("NSE", "EQUITY")
    )
    assert len(results) == 2

    # Test query with LIKE
    results = instrument_query.custom_query("name LIKE ?", ("TEST COMPANY%",))
    assert len(results) == 5  # All test records match this pattern

    # Test query with multiple conditions
    results = instrument_query.custom_query(
        "exchange = ? AND instrument_type = ? AND lot_size > ?", ("NSE", "FUTURES", 50)
    )
    assert len(results) == 1
    assert results[0]["trading_symbol"] == "TESTCO1-FUT-25DEC"

    # Test query for new fields
    results = instrument_query.custom_query("security_type = ?", ("OPTIONS",))
    assert len(results) == 1
    assert results[0]["instrument_type"] == "OPTIONS"

    # Test query with no results
    results = instrument_query.custom_query(
        "exchange = ? AND instrument_type = ?", ("BSE", "FUTURES")
    )
    assert len(results) == 0


def test_get_by_trading_symbol(instrument_query):
    """Test getting instrument by trading symbol."""
    # Test with existing trading symbol
    result = instrument_query.get_by_trading_symbol("TESTCO1")
    assert result is not None
    assert result["instrument_key"] == "NSE_EQ|INE001A01036"

    # Test with exchange filter
    result = instrument_query.get_by_trading_symbol("TESTCO2", exchange="NSE")
    assert result is not None
    assert result["instrument_key"] == "NSE_EQ|INE002A01018"

    # Test with exchange filter that doesn't match
    result = instrument_query.get_by_trading_symbol("TESTCO1", exchange="BSE")
    assert result is None

    # Test with nonexistent trading symbol
    result = instrument_query.get_by_trading_symbol("NONEXISTENT")
    assert result is None


def test_get_option_chain(instrument_query):
    """Test getting option chain for underlying security."""
    # Test with ISIN that has options
    results = instrument_query.get_option_chain("INE001A01036")
    assert len(results) == 1
    assert results[0]["option_type"] == "CE"
    assert results[0]["strike"] == 1100.0

    # Test with expiry filter
    results = instrument_query.get_option_chain("INE001A01036", expiry="2025-12-31")
    assert len(results) == 1

    # Test with different expiry (no matches)
    results = instrument_query.get_option_chain("INE001A01036", expiry="2024-12-31")
    assert len(results) == 0

    # Test with ISIN that has no options
    results = instrument_query.get_option_chain("INVALID")
    assert len(results) == 0
