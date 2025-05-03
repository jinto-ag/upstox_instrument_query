"""Interactive query interface for Upstox Instrument Query.

This module provides an interactive command-line interface for querying
the instrument database through a REPL-like experience.
"""

import cmd
import re
import sys
from typing import Any, Dict, List

from .constants import Exchange, InstrumentType
from .query import InstrumentQuery
from .yfinance import display_ticker_info, get_ticker_info


class InteractiveQuery(cmd.Cmd):
    """
    Interactive command prompt for querying Upstox instrument data.

    This class provides a REPL-like interface for querying the instrument database
    with a set of commands that support advanced filtering and data retrieval.
    """

    intro = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                Upstox Instrument Query                    ║
    ║                Interactive Query Mode                     ║
    ╚═══════════════════════════════════════════════════════════╝
    Type 'help' for a list of commands.
    Type 'exit' or 'quit' to exit.
    """
    prompt = "upstox> "

    def __init__(self, db_path: str):
        """
        Initialize the interactive query interface.

        Args:
            db_path (str): Path to the SQLite database file
        """
        super().__init__()
        self.query = InstrumentQuery(db_path)
        self.last_results: List[Dict[str, Any]] = []

    def emptyline(self):
        """Do nothing on empty line."""

    def do_exit(self, arg):
        """Exit the interactive query session."""
        print("Goodbye!")
        return True

    def do_quit(self, arg):
        """Exit the interactive query session."""
        return self.do_exit(arg)

    def do_EOF(self, arg):
        """Handle EOF (Ctrl+D) to exit cleanly."""
        print()
        return self.do_exit(arg)

    def do_find(self, arg):
        """
        Find instruments by name (supports regex patterns).

        Usage: find PATTERN [--case-sensitive]
        """
        args = arg.split()
        if not args:
            print("Error: Missing name pattern")
            print("Usage: find PATTERN [--case-sensitive]")
            return

        pattern = args[0]
        case_sensitive = "--case-sensitive" in args

        try:
            results = self.query.search_by_name(pattern, case_sensitive=case_sensitive)
            self._display_results(results)
        except re.error as e:
            print(f"Error in regex pattern: {e}")

    def do_exchange(self, arg):
        """
        Find instruments by exchange.

        Usage: exchange EXCHANGE_CODE
        Example: exchange NSE
        """
        if not arg:
            print("Error: Missing exchange code")
            print("Usage: exchange EXCHANGE_CODE")
            print(f"Available exchanges: {', '.join(e.value for e in Exchange)}")
            return

        results = self.query.filter_by_exchange(arg.upper())
        self._display_results(results)

    def do_type(self, arg):
        """
        Find instruments by instrument type.

        Usage: type INSTRUMENT_TYPE
        Example: type EQUITY
        """
        if not arg:
            print("Error: Missing instrument type")
            print("Usage: type INSTRUMENT_TYPE")
            print(f"Available types: {', '.join(t.value for t in InstrumentType)}")
            return

        results = self.query.filter_by_instrument_type(arg.upper())
        self._display_results(results)

    def do_symbol(self, arg):
        """
        Find instrument by trading symbol.

        Usage: symbol TRADING_SYMBOL [EXCHANGE]
        Example: symbol SBIN
        Example: symbol SBIN NSE
        """
        if not arg:
            print("Error: Missing trading symbol")
            print("Usage: symbol TRADING_SYMBOL [EXCHANGE]")
            return

        args = arg.split()
        symbol = args[0]
        exchange = args[1].upper() if len(args) > 1 else None

        result = self.query.get_by_trading_symbol(symbol, exchange=exchange)
        if result:
            self._display_results([result])
        else:
            print(
                f"No instrument found with trading symbol '{symbol}'"
                + (f" on exchange '{exchange}'" if exchange else "")
            )

    def do_key(self, arg):
        """
        Find instrument by instrument key.

        Usage: key INSTRUMENT_KEY
        Example: key NSE_EQ|INE001A01036
        """
        if not arg:
            print("Error: Missing instrument key")
            print("Usage: key INSTRUMENT_KEY")
            return

        result = self.query.get_by_instrument_key(arg)
        if result:
            self._display_results([result])
        else:
            print(f"No instrument found with key '{arg}'")

    def do_isin(self, arg):
        """
        Find instruments by ISIN.

        Usage: isin ISIN_CODE
        Example: isin INE001A01036
        """
        if not arg:
            print("Error: Missing ISIN")
            print("Usage: isin ISIN_CODE")
            return

        results = self.query.filter_by_isin(arg)
        self._display_results(results)

    def do_options(self, arg):
        """
        Find option chain for underlying security.

        Usage: options ISIN [EXPIRY]
        Example: options INE001A01036
        Example: options INE001A01036 2023-06-29
        """
        if not arg:
            print("Error: Missing ISIN")
            print("Usage: options ISIN [EXPIRY]")
            return

        args = arg.split()
        isin = args[0]
        expiry = args[1] if len(args) > 1 else None

        results = self.query.get_option_chain(isin, expiry=expiry)
        self._display_results(results)

    def do_custom(self, arg):
        """
        Execute a custom SQL query.

        Usage: custom SQL_WHERE_CLAUSE [PARAM1 PARAM2 ...]
        Example: custom "exchange = ? AND name LIKE ?" NSE "%RELIANCE%"
        """
        if not arg:
            print("Error: Missing SQL WHERE clause")
            print("Usage: custom SQL_WHERE_CLAUSE [PARAM1 PARAM2 ...]")
            return

        parts = []

        if arg.startswith('"') or arg.startswith("'"):
            quote_char = arg[0]
            quote_end = arg.find(quote_char, 1)

            if quote_end > 0:

                where_clause = arg[1:quote_end]

                rest = arg[quote_end + 1 :].strip()

                params = []
                current_param = ""
                in_param_quotes = False
                param_quote_char = None

                for char in rest:
                    if char in ['"', "'"]:
                        if not in_param_quotes:
                            in_param_quotes = True
                            param_quote_char = char
                        elif char == param_quote_char:
                            in_param_quotes = False
                            param_quote_char = None
                        current_param += char
                    elif char.isspace() and not in_param_quotes:
                        if current_param:

                            if (
                                current_param.startswith('"')
                                and current_param.endswith('"')
                            ) or (
                                current_param.startswith("'")
                                and current_param.endswith("'")
                            ):
                                current_param = current_param[1:-1]
                            params.append(current_param)
                            current_param = ""
                    else:
                        current_param += char

                if current_param:

                    if (
                        current_param.startswith('"') and current_param.endswith('"')
                    ) or (
                        current_param.startswith("'") and current_param.endswith("'")
                    ):
                        current_param = current_param[1:-1]
                    params.append(current_param)
            else:

                where_clause = arg.strip("\"'")
                params = []
        else:

            parts = arg.split(None, 1)
            where_clause = parts[0]

            if len(parts) > 1:

                params = []
                current_param = ""
                in_param_quotes = False
                param_quote_char = None

                for char in parts[1]:
                    if char in ['"', "'"]:
                        if not in_param_quotes:
                            in_param_quotes = True
                            param_quote_char = char
                        elif char == param_quote_char:
                            in_param_quotes = False
                            param_quote_char = None
                        current_param += char
                    elif char.isspace() and not in_param_quotes:
                        if current_param:

                            if (
                                current_param.startswith('"')
                                and current_param.endswith('"')
                            ) or (
                                current_param.startswith("'")
                                and current_param.endswith("'")
                            ):
                                current_param = current_param[1:-1]
                            params.append(current_param)
                            current_param = ""
                    else:
                        current_param += char

                if current_param:

                    if (
                        current_param.startswith('"') and current_param.endswith('"')
                    ) or (
                        current_param.startswith("'") and current_param.endswith("'")
                    ):
                        current_param = current_param[1:-1]
                    params.append(current_param)
            else:
                params = []

        try:
            results = self.query.custom_query(where_clause, tuple(params))
            self._display_results(results)
        except Exception as e:
            print(f"Error executing query: {e}")

    def do_detail(self, arg):
        """
        Show detailed information for an instrument from the last result set.

        Usage: detail INDEX
        Example: detail 0
        """
        if not arg:
            print("Error: Missing result index")
            print("Usage: detail INDEX")
            return

        try:
            index = int(arg)
            if not self.last_results:
                print("No results available. Run a query first.")
                return

            if index < 0 or index >= len(self.last_results):
                print(
                    f"Error: Index out of range. Valid range: 0-{len(self.last_results) - 1}"
                )
                return

            self._display_detail(self.last_results[index])
        except ValueError:
            print("Error: INDEX must be a number")

    def do_ticker(self, arg):
        """
        Get Yahoo Finance ticker information for a symbol.

        Usage: ticker SYMBOL
        Example: ticker AAPL
        Example: ticker RELIANCE.NS
        """
        if not arg:
            print("Error: Missing ticker symbol")
            print("Usage: ticker SYMBOL")
            return

        ticker_info = get_ticker_info(arg)
        if ticker_info:
            display_ticker_info(ticker_info)

            instruments = self.query.search_by_name(arg.split(".")[0])
            if instruments:
                print("\nCorresponding Upstox Instruments:")
                self._display_results(instruments[:5])
        else:
            print(f"No information found for ticker '{arg}'")

    def _display_results(self, results: List[Dict[str, Any]]) -> None:
        """
        Display query results in a tabular format.

        Args:
            results: List of instrument dictionaries
        """
        self.last_results = results

        if not results:
            print("No results found")
            return

        fields = [
            "instrument_key",
            "name",
            "trading_symbol",
            "exchange",
            "instrument_type",
        ]

        print(f"\nFound {len(results)} results:\n")
        header = "  # | " + " | ".join(f"{field.upper()}" for field in fields)
        print(header)
        print("-" * len(header))

        for i, instrument in enumerate(results[:20]):
            values = []
            for field in fields:
                value = instrument.get(field, "N/A")

                if isinstance(value, str) and len(value) > 20:
                    value = value[:17] + "..."
                values.append(str(value))

            print(f"{i:3d} | " + " | ".join(values))

        if len(results) > 20:
            print(f"\n...and {len(results) - 20} more results")

        print("\nUse 'detail INDEX' to see more information about a specific result.")

    def _display_detail(self, instrument: Dict[str, Any]) -> None:
        """
        Display detailed information for a single instrument.

        Args:
            instrument: Instrument dictionary
        """
        if not instrument:
            print("No instrument data available")
            return

        print("\n=== Instrument Details ===")

        basic_fields = [
            ("Instrument Key", "instrument_key"),
            ("Name", "name"),
            ("Trading Symbol", "trading_symbol"),
            ("Exchange", "exchange"),
            ("Instrument Type", "instrument_type"),
            ("Segment", "segment"),
            ("ISIN", "isin"),
        ]

        for label, field in basic_fields:
            value = instrument.get(field, "N/A")
            print(f"{label}: {value}")

        if instrument.get("instrument_type") in ["FUTURES", "OPTIONS"]:
            print("\n--- Contract Details ---")
            for field in ["expiry", "lot_size", "tick_size"]:
                value = instrument.get(field, "N/A")
                print(f"{field.title()}: {value}")

        if instrument.get("instrument_type") == "OPTIONS":
            print("\n--- Option Specifics ---")
            for field in ["option_type", "strike"]:
                value = instrument.get(field, "N/A")
                print(f"{field.title().replace('_', ' ')}: {value}")

        if "last_price" in instrument:
            print("\n--- Price Details ---")
            print(f"Last Price: {instrument.get('last_price', 'N/A')}")

        print("\n--- Other Details ---")
        other_fields = (
            set(instrument.keys())
            - {field for _, field in basic_fields}
            - {
                "expiry",
                "lot_size",
                "tick_size",
                "option_type",
                "strike",
                "last_price",
            }
        )

        for field in sorted(other_fields):
            value = instrument.get(field, "N/A")
            print(f"{field.replace('_', ' ').title()}: {value}")

        print("=" * 40)


def start_interactive_session(db_path: str) -> None:
    """
    Start an interactive query session.

    Args:
        db_path (str): Path to the SQLite database file
    """
    try:
        InteractiveQuery(db_path).cmdloop()
    except KeyboardInterrupt:
        print("\nSession terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error during interactive session: {e}")
        sys.exit(1)
