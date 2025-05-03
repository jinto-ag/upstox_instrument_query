"""YFinance ticker integration for Upstox Instrument Query.

This module provides functionality to lookup stock details using
the Yahoo Finance API through the yfinance package.
"""

import datetime
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

try:
    import yfinance as yf
except ImportError:
    yf = None


logger = logging.getLogger(__name__)


def get_ticker_info(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information for a stock ticker from Yahoo Finance.

    Args:
        ticker_symbol (str): Yahoo Finance ticker symbol

    Returns:
        Optional[Dict[str, Any]]: Dictionary with ticker info or None if not found
    """
    if yf is None:
        logger.error(
            "yfinance package not installed. Install with 'pip install yfinance'"
        )
        print(
            "Error: yfinance package not installed. Install with 'pip install yfinance'"
        )
        return None

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        if not info or "regularMarketPrice" not in info:
            logger.warning(f"Could not retrieve information for ticker {ticker_symbol}")
            return None

        return info
    except Exception as e:
        logger.error(f"Error retrieving ticker {ticker_symbol}: {str(e)}")
        return None


def find_corresponding_instrument(
    query: Any, ticker_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Find corresponding instrument in the Upstox database based on Yahoo Finance ticker info.

    Args:
        query: InstrumentQuery instance
        ticker_info (Dict[str, Any]): Yahoo Finance ticker information

    Returns:
        List[Dict[str, Any]]: List of matching instruments
    """
    if not ticker_info:
        return []

    company_name = ticker_info.get("shortName") or ticker_info.get("longName")
    if not company_name:
        return []

    instruments = []

    name_results = query.search_by_name(company_name.split()[0])
    if name_results:
        instruments.extend(name_results)

    symbol = ticker_info.get("symbol", "")
    pure_symbol = ""

    if "." in symbol:
        pure_symbol = symbol.split(".")[0]
    else:
        pure_symbol = symbol

    if pure_symbol:
        trading_symbol = query.get_by_trading_symbol(pure_symbol)
        if trading_symbol:
            instruments.append(trading_symbol)

        if "." in symbol and not any(
            i.get("trading_symbol") == pure_symbol for i in instruments
        ):
            symbol_results = query.search_by_name(
                f"^{pure_symbol}$", case_sensitive=False
            )
            if symbol_results:
                for result in symbol_results:
                    if result not in instruments:
                        instruments.append(result)

    return instruments


def display_ticker_info(ticker_info: Dict[str, Any]) -> None:
    """
    Display formatted ticker information from Yahoo Finance.

    Args:
        ticker_info (Dict[str, Any]): Yahoo Finance ticker information
    """
    if not ticker_info:
        print("No ticker information available")
        return

    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    print("\n=== Yahoo Finance Ticker Information ===")
    print(f"Data as of: {formatted_time}")
    print(f"Name: {ticker_info.get('shortName') or ticker_info.get('longName', 'N/A')}")
    print(f"Symbol: {ticker_info.get('symbol', 'N/A')}")
    print(f"Exchange: {ticker_info.get('exchange', 'N/A')}")
    print(f"Current Price: {ticker_info.get('regularMarketPrice', 'N/A')}")
    print(f"Previous Close: {ticker_info.get('regularMarketPreviousClose', 'N/A')}")
    print(f"Open: {ticker_info.get('regularMarketOpen', 'N/A')}")
    print(
        f"Day Range: {ticker_info.get('regularMarketDayLow', 'N/A')} - "
        f"{ticker_info.get('regularMarketDayHigh', 'N/A')}"
    )
    print(
        f"52 Week Range: {ticker_info.get('fiftyTwoWeekLow', 'N/A')} - "
        f"{ticker_info.get('fiftyTwoWeekHigh', 'N/A')}"
    )
    print(f"Market Cap: {ticker_info.get('marketCap', 'N/A')}")
    print(f"Volume: {ticker_info.get('regularMarketVolume', 'N/A')}")

    if "trailingPE" in ticker_info:
        print(f"P/E Ratio: {ticker_info.get('trailingPE', 'N/A')}")

    if "dividendYield" in ticker_info and ticker_info["dividendYield"] is not None:
        print(f"Dividend Yield: {ticker_info.get('dividendYield', 0) * 100:.2f}%")

    print("=" * 40)


def display_corresponding_instruments(instruments: List[Dict[str, Any]]) -> None:
    """
    Display corresponding Upstox instruments in a categorized format.

    Args:
        instruments (List[Dict[str, Any]]): List of matching instruments
    """
    if not instruments:
        print("\nNo corresponding instruments found in Upstox database.")
        return

    grouped = defaultdict(list)
    for instrument in instruments:
        instr_type = instrument.get("instrument_type", "UNKNOWN")
        grouped[instr_type].append(instrument)

    print("\nCorresponding Upstox Instruments:")

    types_found = list(grouped.keys())
    if types_found:
        print(f"Available Instrument Types: {', '.join(types_found)}")

    if "EQ" in grouped:
        equity = grouped["EQ"][0]
        print("\n== EQUITY ==")
        print(f"Upstox Equity Instrument Key: {equity.get('instrument_key', 'N/A')}")
        print(f"Trading Symbol: {equity.get('trading_symbol', 'N/A')}")
        print(f"Exchange: {equity.get('exchange', 'N/A')}")
        print(f"ISIN: {equity.get('isin', 'N/A')}")

    for instr_type, instruments_list in grouped.items():
        if instr_type == "EQ":
            continue

        print(f"\n== {instr_type} ==")
        print(f"Count: {len(instruments_list)}")

        for i, instrument in enumerate(instruments_list[:3]):
            print(f"\n{i + 1}. Key: {instrument.get('instrument_key', 'N/A')}")
            print(f"   Trading Symbol: {instrument.get('trading_symbol', 'N/A')}")
            print(f"   Name: {instrument.get('name', 'N/A')}")

            if instr_type in ["CE", "PE"]:
                print(f"   Option Type: {instrument.get('option_type', 'N/A')}")
                print(f"   Strike Price: {instrument.get('strike', 'N/A')}")
                print(f"   Expiry: {instrument.get('expiry', 'N/A')}")
            elif instr_type == "FUTURES":
                print(f"   Expiry: {instrument.get('expiry', 'N/A')}")
                print(f"   Lot Size: {instrument.get('lot_size', 'N/A')}")

        if len(instruments_list) > 3:
            print(f"\n...and {len(instruments_list) - 3} more {instr_type} instruments")

    print("\nFor detailed instrument information, try:")
    print("upstox-query q -k <instrument_key>  # Get details for a specific instrument")
    print("or")
    print("upstox-query interactive  # Start interactive mode for advanced queries")
