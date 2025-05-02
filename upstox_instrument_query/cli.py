#!/usr/bin/env python3
"""Command-line interface for Upstox Instrument Query.

This module provides command-line utilities for initializing and updating
the instrument database from JSON files or URLs.
"""

import argparse
import sys

from upstox_instrument_query.database import InstrumentDatabase


def main():
    """Entry point for the command-line interface.

    Parses arguments and executes the appropriate command.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Upstox Instrument Query - Efficiently manage and query Upstox "
            "instrument data"
        )
    )
    subparsers = parser.add_subparsers(dest="command")

    # Initialize database command
    init_parser = subparsers.add_parser(
        "init", help="Initialize database from JSON file or URL"
    )
    init_parser.add_argument("json_source", help="Path to instruments JSON file or URL")
    init_parser.add_argument("db_path", help="Path to SQLite database file")
    init_parser.add_argument(
        "--url", action="store_true", help="Treat json_source as a URL"
    )

    # Update database command
    update_parser = subparsers.add_parser(
        "update", help="Update database from JSON file or URL"
    )
    update_parser.add_argument(
        "json_source", help="Path to instruments JSON file or URL"
    )
    update_parser.add_argument("db_path", help="Path to SQLite database file")
    update_parser.add_argument(
        "--url", action="store_true", help="Treat json_source as a URL"
    )

    args = parser.parse_args()

    if args.command == "init":
        try:
            db = InstrumentDatabase(args.db_path)
            db.initialize(args.json_source, is_url=args.url)
            print(f"Database successfully initialized at {args.db_path}")
        except Exception as e:
            print(f"Error initializing database: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "update":
        try:
            db = InstrumentDatabase(args.db_path)
            db.update_instruments(args.json_source, is_url=args.url)
            print(f"Database successfully updated at {args.db_path}")
        except Exception as e:
            print(f"Error updating database: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
