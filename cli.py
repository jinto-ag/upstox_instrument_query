import argparse

from upstox_instrument_query.upstox_instrument_query.database import InstrumentDatabase


def main():
    parser = argparse.ArgumentParser(description="Upstox Instrument Query CLI")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser(
        "init", help="Initialize database from JSON file or URL"
    )
    init_parser.add_argument("json_source", help="Path to instruments JSON file or URL")
    init_parser.add_argument("db_path", help="Path to SQLite database file")
    init_parser.add_argument(
        "--url", action="store_true", help="Treat json_source as a URL"
    )

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
        db = InstrumentDatabase(args.db_path)
        db.initialize(args.json_source, is_url=args.url)
        print(f"Database initialized at {args.db_path}")
    elif args.command == "update":
        db = InstrumentDatabase(args.db_path)
        db.connect()
        db.cursor.execute("DELETE FROM instruments")
        if args.url:
            db._load_json_from_url(args.json_source)
        else:
            db._load_json(args.json_source)
        db.conn.commit()
        print(f"Database updated at {args.db_path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
