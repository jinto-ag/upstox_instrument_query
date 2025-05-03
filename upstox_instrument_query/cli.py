"""Command-line interface for Upstox Instrument Query.

This module provides command-line utilities for initializing, updating,
and querying the instrument database from JSON files or URLs.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List

from upstox_instrument_query.constants import DEFAULT_DB_PATH, DEFAULT_INSTRUMENTS_URL
from upstox_instrument_query.database import InstrumentDatabase
from upstox_instrument_query.interactive import start_interactive_session
from upstox_instrument_query.logging_config import (
    archive_logs,
    clean_old_archives,
    clear_logs,
    get_logger,
    list_available_logs,
    view_logs,
)
from upstox_instrument_query.query import InstrumentQuery
from upstox_instrument_query.yfinance import (
    display_ticker_info,
    find_corresponding_instrument,
    get_ticker_info,
)

logger = get_logger("main")


def display_results(results: List[Dict[str, Any]], format_json: bool = False) -> None:
    """
    Display query results in a user-friendly format.

    Args:
        results: List of instrument dictionaries
        format_json: Whether to output in JSON format
    """
    if not results:
        print("No results found")
        return

    if format_json:
        print(json.dumps(results, indent=2))
        return

    print(f"\nFound {len(results)} results:\n")

    fields = [
        "instrument_key",
        "name",
        "trading_symbol",
        "exchange",
        "instrument_type",
    ]

    header = " | ".join(f"{field.upper()}" for field in fields)
    print(header)
    print("-" * len(header))

    for instrument in results[:20]:
        values = []
        for field in fields:
            value = instrument.get(field, "N/A")

            if isinstance(value, str) and len(value) > 20:
                value = value[:17] + "..."
            values.append(str(value))

        print(" | ".join(values))

    if len(results) > 20:
        print(f"\n...and {len(results) - 20} more results")


def query_command(args) -> None:
    """
    Execute a query command based on command-line arguments.

    Args:
        args: Command-line arguments
    """
    try:

        args.db_path = InstrumentDatabase.ensure_database_exists(args.db_path)

        query = InstrumentQuery(args.db_path)

        results = []

        if args.instrument_key:
            result = query.get_by_instrument_key(args.instrument_key)
            if result:
                results = [result]
        elif args.exchange:
            results = query.filter_by_exchange(args.exchange)
        elif args.instrument_type:
            results = query.filter_by_instrument_type(args.instrument_type)
        elif args.segment:
            results = query.filter_by_segment(args.segment)
        elif args.isin:
            results = query.filter_by_isin(args.isin)
        elif args.option_type:
            results = query.filter_by_option_type(args.option_type)
        elif args.name:
            results = query.search_by_name(
                args.name, case_sensitive=args.case_sensitive
            )
        elif args.trading_symbol:
            result = query.get_by_trading_symbol(
                args.trading_symbol, exchange=args.exchange
            )
            if result:
                results = [result]
        elif args.option_chain:
            results = query.get_option_chain(args.option_chain, expiry=args.expiry)
        elif args.where:

            params = []
            if args.params:
                for param in args.params:
                    try:

                        if param.isdigit():
                            params.append(int(param))
                        elif param.replace(".", "", 1).isdigit():
                            params.append(param)
                        else:
                            params.append(param)
                    except (ValueError, TypeError):
                        params.append(param)

            results = query.custom_query(args.where, tuple(params))

        display_results(results, format_json=args.json)

    except Exception as e:
        print(f"Error executing query: {e}", file=sys.stderr)
        sys.exit(1)


def yfinance_command(args) -> None:
    """
    Execute a Yahoo Finance ticker query based on command-line arguments.

    Args:
        args: Command-line arguments
    """
    try:

        args.db_path = InstrumentDatabase.ensure_database_exists(args.db_path)

        ticker_info = get_ticker_info(args.ticker)
        if ticker_info:
            display_ticker_info(ticker_info)

            query = InstrumentQuery(args.db_path)
            instruments = find_corresponding_instrument(query, ticker_info)

            if not args.find_instruments and instruments:
                eq_instruments = [
                    i for i in instruments if i.get("instrument_type") == "EQ"
                ]
                if eq_instruments:

                    print("\n=== Corresponding Upstox Equity ===")
                    equity = eq_instruments[0]
                    print(f"Instrument Key: {equity.get('instrument_key', 'N/A')}")
                    print(f"Trading Symbol: {equity.get('trading_symbol', 'N/A')}")
                    print(f"Exchange: {equity.get('exchange', 'N/A')}")
                    print(f"ISIN: {equity.get('isin', 'N/A')}")
                    print(f"Lot Size: {equity.get('lot_size', 'N/A')}")
                    print(f"Tick Size: {equity.get('tick_size', 'N/A')}")
                    print("=" * 40)

                    print(
                        "\nTip: Use --find-instruments to see all related instruments "
                        "(futures, options, etc.)"
                    )

            elif args.find_instruments:
                from upstox_instrument_query.yfinance import (
                    display_corresponding_instruments,
                )

                display_corresponding_instruments(instruments)
        else:
            print(f"No information found for ticker '{args.ticker}'")
            sys.exit(1)
    except Exception as e:
        print(f"Error retrieving ticker information: {e}", file=sys.stderr)
        sys.exit(1)


def interactive_command(args) -> None:
    """
    Start an interactive query session.

    Args:
        args: Command-line arguments
    """
    try:

        args.db_path = InstrumentDatabase.ensure_database_exists(args.db_path)
        start_interactive_session(args.db_path)
    except Exception as e:
        print(f"Error in interactive session: {e}", file=sys.stderr)
        sys.exit(1)


def logs_command(args) -> None:
    """
    Execute log management commands based on command-line arguments.

    Args:
        args: Command-line arguments
    """
    try:
        if args.clear:
            logger.info("Clearing logs per user request")
            cleared_files = clear_logs(args.log_name)
            print(f"Cleared {len(cleared_files)} log files")
            for file in cleared_files[:5]:
                print(f"  - {os.path.basename(file)}")
            if len(cleared_files) > 5:
                print(f"  - ...and {len(cleared_files) - 5} more")

        elif args.archive:
            logger.info("Archiving logs per user request")
            archive_path = archive_logs()
            print(f"Logs archived to: {archive_path}")

        elif args.clean_archives:
            logger.info(f"Cleaning log archives older than {args.days} days")
            removed_files = clean_old_archives(days=args.days)
            if removed_files:
                print(f"Removed {len(removed_files)} old archive files")
            else:
                print("No old archive files to remove")

        elif args.list:

            log_files = list_available_logs()
            print("Available log files:")
            print("=" * 80)

            for log_name, files in log_files.items():
                if files:
                    print(f"\n{log_name.upper()} LOGS:")
                    for idx, file_info in enumerate(files):
                        path = file_info["path"]
                        size_kb = file_info["size"] / 1024
                        modified = file_info["modified"]
                        is_rotated = ".log." in path
                        rotated_info = " (rotated)" if is_rotated else ""

                        print(f"  {idx + 1}. {os.path.basename(path)}{rotated_info}")
                        print(
                            f"     Size: {size_kb:.1f} KB | Last modified: {modified}"
                        )
                else:
                    print(f"\n{log_name.upper()} LOGS: No logs found")

            print(
                "\nUse 'upstox-query logs --view --log-name <name>' to view a specific log"
            )

        elif args.view:

            log_lines = view_logs(
                log_name=args.log_name,
                head=args.head,
                tail=args.tail,
                search_pattern=args.search,
                show_rotated=args.show_rotated,
            )

            if log_lines:
                log_name = args.log_name or "main"

                filters = []
                if args.head:
                    filters.append(f"first {args.head} lines")
                if args.tail:
                    filters.append(f"last {args.tail} lines")
                if args.search:
                    filters.append(f"matching '{args.search}'")

                filter_str = f" ({', '.join(filters)})" if filters else ""
                rotated_str = " (including rotated logs)" if args.show_rotated else ""

                print(f"=== {log_name.upper()} LOG{filter_str}{rotated_str} ===\n")

                for line in log_lines:
                    print(line.rstrip())

                print(f"\n=== End of {log_name.upper()} LOG ===")
                print(f"Displayed {len(log_lines)} lines")
            else:
                print("No log entries found matching your criteria")

        else:
            print(
                "No log action specified."
                " Use --clear, --archive, --clean-archives, --view, or --list"
            )

    except Exception as e:
        logger.error(f"Error managing logs: {e}", exc_info=True)
        print(f"Error managing logs: {e}", file=sys.stderr)
        sys.exit(1)


def cache_command(args) -> None:
    """
    Execute cache management commands based on command-line arguments.

    Args:
        args: Command-line arguments
    """
    try:
        args.db_path = InstrumentDatabase.ensure_database_exists(args.db_path)
        query = InstrumentQuery(args.db_path)

        logger.info("Clearing query cache per user request")
        query.clear_cache()
        print("Query cache cleared successfully")

    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        print(f"Error clearing cache: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Entry point for the command-line interface.

    Parses arguments and executes the appropriate command.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Upstox Instrument Query - Efficiently manage and query Upstox "
            "instrument data.\n\n"
            "This tool provides a command-line interface for working with Upstox "
            "instrument data, including database setup, powerful querying capabilities, "
            "and integration with Yahoo Finance. It also offers comprehensive logging "
            "and caching features for optimal performance."
        ),
        epilog=(
            "Examples:\n"
            "  # Database Management:\n"
            "  upstox-query init                        # Initialize database with default "
            "settings\n"
            "  upstox-query init /path/to/data.json     # Initialize with custom JSON file\n"
            "  upstox-query update                      # Update database with latest "
            "instruments\n\n"
            "  # Querying:\n"
            '  upstox-query q -n "RELIANCE"             # Search for instruments with name "'
            '"containing "RELIANCE"\n'
            "  upstox-query query -e NSE                # List all NSE instruments\n"
            "  upstox-query query -i INE001A01036       # Find instruments by ISIN\n"
            "  upstox-query query -t EQ                 # Find all equity instruments\n"
            "  upstox-query query -s NSE_FO             # Find all NSE futures & options\n"
            "  upstox-query query -o CE                 # Find all call options\n"
            '  upstox-query query -w "name LIKE ?" -p "%BANK%"  # Custom SQL query\n\n'
            "  # Yahoo Finance Integration:\n"
            "  upstox-query ticker SBIN.NS              # Get Yahoo Finance data for SBI\n"
            "  upstox-query t RELIANCE.NS --find-instruments  # Find all related Upstox "
            "instruments\n\n"
            "  # Interactive Mode:\n"
            "  upstox-query i                           # Start interactive query session\n\n"
            "  # Log Management:\n"
            "  upstox-query logs --list                 # List all available log files\n"
            "  upstox-query logs --view                 # View main log contents\n"
            "  upstox-query logs --view --tail 20       # View last 20 lines of main log\n"
            "  upstox-query logs --clear                # Clear all logs\n\n"
            "  # Cache Management:\n"
            "  upstox-query cache                       # Clear query cache for better "
            "performance\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--db-path",
        help=f"Path to SQLite database file (default: {DEFAULT_DB_PATH})",
        default=DEFAULT_DB_PATH,
    )

    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser(
        "init",
        help="Initialize database from JSON file or URL",
        description=(
            "Initialize a new SQLite database with Upstox instrument data. "
            "This command creates a new database file and populates it with instrument "
            "data from either a JSON file or a URL. This is typically the first command "
            "you should run when setting up the tool."
        ),
        epilog=(
            "Examples:\n"
            "  upstox-query init                        # Use default URL source\n"
            "  upstox-query init /path/to/data.json     # Use local JSON file\n"
            "  upstox-query init https://example.com/instruments.json --url  # Use custom URL\n"
            "  upstox-query init --db-path ~/custom_path.sqlite  # Specify database location\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    init_parser.add_argument(
        "json_source",
        nargs="?",
        help=(
            f"Path to instruments JSON file or URL "
            f"(default: {DEFAULT_INSTRUMENTS_URL})"
        ),
        default=DEFAULT_INSTRUMENTS_URL,
    )

    init_parser.add_argument(
        "db_path_positional",
        nargs="?",
        help="Path to SQLite database file (deprecated, use --db-path instead)",
    )
    init_parser.add_argument(
        "--url",
        action="store_true",
        help="Treat json_source as a URL",
        default=False,
    )

    update_parser = subparsers.add_parser(
        "update",
        help="Update database from JSON file or URL",
        description=(
            "Update an existing SQLite database with the latest Upstox instrument data. "
            "This command refreshes the data in your database without recreating it. "
            "You can specify a custom JSON file or URL source for the update."
        ),
        epilog=(
            "Examples:\n"
            "  upstox-query update                      # Update from default URL source\n"
            "  upstox-query update /path/to/data.json   # Update from local JSON file\n"
            "  upstox-query update --db-path ~/custom_path.sqlite  # Update specific database\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    update_parser.add_argument(
        "json_source",
        nargs="?",
        help=(
            f"Path to instruments JSON file or URL "
            f"(default: {DEFAULT_INSTRUMENTS_URL})"
        ),
        default=DEFAULT_INSTRUMENTS_URL,
    )

    update_parser.add_argument(
        "db_path_positional",
        nargs="?",
        help="Path to SQLite database file (deprecated, use --db-path instead)",
    )
    update_parser.add_argument(
        "--url",
        action="store_true",
        help="Treat json_source as a URL",
        default=False,
    )

    query_parser = subparsers.add_parser(
        "query",
        help="Query instrument data from the database",
        description=(
            "Query and filter Upstox instrument data using various search criteria. "
            "This command allows you to search for instruments by name, exchange, type, "
            "ISIN, and many other attributes. Results are displayed in a tabular format "
            "by default, or can be output as JSON for further processing."
        ),
        epilog=(
            "Examples:\n"
            '  upstox-query query -n "RELIANCE"         # Search by name (supports regex)\n'
            "  upstox-query query -e NSE                # List all NSE instruments\n"
            "  upstox-query query -t EQ                 # List all equity instruments\n"
            "  upstox-query query -s NSE_FO             # List all NSE F&O instruments\n"
            "  upstox-query query -i INE001A01036       # Find instruments by ISIN\n"
            "  upstox-query query -o CE                 # List all call options\n"
            "  upstox-query query -y RELIANCE           # Find by trading symbol\n"
            "  upstox-query query -c INE123456789       # Get option chain for an ISIN\n"
            '  upstox-query query -w "name LIKE ? AND exchange = ?" -p "%BANK%" NSE  '
            "# Custom query\n"
            "  upstox-query query -n bank --json        # Output results in JSON format\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    query_group = query_parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument("-k", "--instrument-key", help="Query by instrument key")
    query_group.add_argument("-e", "--exchange", help="Query by exchange")
    query_group.add_argument("-t", "--instrument-type", help="Query by instrument type")
    query_group.add_argument("-s", "--segment", help="Query by segment")
    query_group.add_argument("-i", "--isin", help="Query by ISIN")
    query_group.add_argument("-o", "--option-type", help="Query by option type (CE/PE)")
    query_group.add_argument(
        "-n", "--name", help="Search by name (supports regex patterns)"
    )
    query_group.add_argument("-y", "--trading-symbol", help="Query by trading symbol")
    query_group.add_argument("-c", "--option-chain", help="Get option chain for ISIN")
    query_group.add_argument("-w", "--where", help="Custom SQL WHERE clause")
    query_group.add_argument("-q", "--query", dest="name", help="Alias for --name")

    query_parser.add_argument(
        "--expiry", help="Filter by expiry date (format: YYYY-MM-DD)"
    )
    query_parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Enable case-sensitive search for name patterns",
    )
    query_parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )
    query_parser.add_argument("--params", nargs="+", help="Parameters for custom query")

    yfinance_parser = subparsers.add_parser(
        "ticker",
        help="Get stock details from Yahoo Finance",
        description=(
            "Retrieve detailed stock information from Yahoo Finance and find corresponding "
            "instruments in the Upstox database. This command allows you to search for a stock "
            "using its Yahoo Finance ticker symbol and view relevant market data. You can also "
            "discover all related Upstox instruments (equity, futures, options) for the stock."
        ),
        epilog=(
            "Examples:\n"
            "  upstox-query ticker SBIN.NS              # Get Yahoo Finance data for SBI\n"
            "  upstox-query t RELIANCE.NS               # Using the short alias 't'\n"
            "  upstox-query ticker HDFCBANK.NS --find-instruments  # Show all related instruments\n"
            "  upstox-query ticker AAPL                 # Get data for international stocks too\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    yfinance_parser.add_argument("ticker", help="Yahoo Finance ticker symbol")
    yfinance_parser.add_argument(
        "--find-instruments",
        action="store_true",
        help="Find corresponding instruments in Upstox database",
    )
    yfinance_parser.add_argument(
        "-yt",
        "--yfinance-ticker",
        dest="ticker",
        help="Alias for ticker argument",
    )

    interactive_parser = subparsers.add_parser(
        "interactive",
        help="Start interactive query session",
        description=(
            "Start an interactive query session with a menu-driven interface. "
            "This mode provides a user-friendly way to explore and query the Upstox "
            "instrument database without needing to remember command-line arguments. "
            "It's ideal for exploring the data or performing multiple queries in sequence."
        ),
        epilog=(
            "Examples:\n"
            "  upstox-query interactive           # Start the interactive session\n"
            "  upstox-query i                     # Using the short alias 'i'\n"
            "  upstox-query i --db-path ~/my_custom_db.sqlite  # Use a custom database\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers.add_parser(
        "i",
        help="Alias for interactive mode",
        parents=[interactive_parser],
        add_help=False,
    )
    subparsers.add_parser(
        "q",
        help="Alias for query mode",
        parents=[query_parser],
        add_help=False,
    )
    subparsers.add_parser(
        "t",
        help="Alias for ticker mode",
        parents=[yfinance_parser],
        add_help=False,
    )

    logs_parser = subparsers.add_parser(
        "logs",
        help="Manage log files (view, clear, archive)",
        description=(
            "View and manage application logs. This command provides comprehensive features for "
            "working with log files including viewing log contents with filtering options, "
            "clearing logs, creating archives, and managing log retention. Logs are automatically "
            "created during application usage and can help with troubleshooting and monitoring."
        ),
        epilog=(
            "Examples:\n"
            "  # Viewing logs:\n"
            "  upstox-query logs --list                 # List all available log files\n"
            "  upstox-query logs --view                 # View main log contents\n"
            "  upstox-query logs --view --head 10       # View first 10 lines of main log\n"
            "  upstox-query logs --view --tail 20       # View last 20 lines of main log\n"
            "  upstox-query logs --view --search ERROR  # View only lines with 'ERROR'\n"
            "  upstox-query logs --view --log-name database  # View database-specific logs\n"
            "  upstox-query logs --view --show-rotated  # View current and rotated logs\n\n"
            "  # Managing logs:\n"
            "  upstox-query logs --clear                # Clear all logs\n"
            "  upstox-query logs --clear --log-name api_calls  # Clear only API logs\n"
            "  upstox-query logs --archive              # Archive logs to a zip file\n"
            "  upstox-query logs --clean-archives --days 15  # Remove archives older than 15 days\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    logs_parser.add_argument("--clear", action="store_true", help="Clear log files")
    logs_parser.add_argument("--archive", action="store_true", help="Archive log files")
    logs_parser.add_argument(
        "--clean-archives", action="store_true", help="Clean old log archives"
    )
    logs_parser.add_argument(
        "--days", type=int, default=30, help="Number of days to keep log archives"
    )
    logs_parser.add_argument(
        "--log-name", help="Specify log name for operations on specific logs"
    )

    logs_parser.add_argument("--view", action="store_true", help="View log files")
    logs_parser.add_argument(
        "--list", action="store_true", help="List available log files"
    )
    logs_parser.add_argument(
        "--head", type=int, help="Show the first N lines of log file"
    )
    logs_parser.add_argument(
        "--tail", type=int, help="Show the last N lines of log file"
    )
    logs_parser.add_argument("--search", help="Search for pattern in log files")
    logs_parser.add_argument(
        "--show-rotated", action="store_true", help="Include rotated logs in view"
    )

    subparsers.add_parser(
        "cache",
        help="Manage query cache (clear)",
        description=(
            "Manage the query results cache to optimize performance. The query system "
            "uses an LRU (Least Recently Used) cache to store query results and improve "
            "response times for frequently used queries. This command allows you to clear "
            "the cache when needed, which can be useful after database updates or when "
            "troubleshooting issues."
        ),
        epilog=(
            "Examples:\n"
            "  upstox-query cache                       # Clear all cached query results\n"
            "  upstox-query cache --db-path ~/custom_db.sqlite  # Clear cache for a "
            "specific database\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    args = parser.parse_args()

    if hasattr(args, "db_path_positional") and args.db_path_positional:
        args.db_path = args.db_path_positional

    if (
        hasattr(args, "json_source")
        and args.json_source
        and (
            args.json_source.startswith("http://")
            or args.json_source.startswith("https://")
        )
    ):
        args.url = True

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "init":
        try:
            db = InstrumentDatabase(args.db_path)
            if args.url:
                db.initialize(args.json_source, is_url=True)
            else:
                db.initialize(args.json_source, is_url=False)
            print(f"Database successfully initialized at {args.db_path}")
        except Exception as e:
            print(f"Error initializing database: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "update":
        try:

            if not os.path.exists(args.db_path):
                print(
                    f"Error: Database file not found at {args.db_path}", file=sys.stderr
                )
                print(
                    "Initialize the database first with: upstox-query init",
                    file=sys.stderr,
                )
                sys.exit(1)

            db = InstrumentDatabase(args.db_path)
            if args.url:
                db.update_instruments(args.json_source, is_url=True)
            else:
                db.update_instruments(args.json_source, is_url=False)
            print(f"Database successfully updated at {args.db_path}")
        except Exception as e:
            print(f"Error updating database: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command in ["query", "q"]:
        query_command(args)
    elif args.command in ["ticker", "t"]:
        yfinance_command(args)
    elif args.command in ["interactive", "i"]:
        interactive_command(args)
    elif args.command == "logs":
        logs_command(args)
    elif args.command == "cache":
        cache_command(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
