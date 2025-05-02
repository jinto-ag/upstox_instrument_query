# Upstox Instrument Query

[![PyPI version](https://img.shields.io/pypi/v/upstox-instrument-query.svg)](https://pypi.org/project/upstox-instrument-query/)
[![Python versions](https://img.shields.io/pypi/pyversions/upstox-instrument-query.svg)](https://pypi.org/project/upstox-instrument-query/)
[![License](https://img.shields.io/github/license/jinto-ag/upstox_instrument_query.svg)](https://github.com/jinto-ag/upstox_instrument_query/blob/main/LICENSE)

A Python package to efficiently query large Upstox instruments JSON files (~60MB) using SQLite for optimal performance.

## Features

- **Memory Efficient**: Streams JSON parsing for minimal memory footprint
- **High Performance**: Uses SQLite with optimized indexes
- **Flexible**: Query by instrument key, exchange, instrument type, or custom criteria
- **Caching**: Implements LRU caching for frequently accessed queries
- **CLI Support**: Command-line tools for database initialization and updates
- **URL Support**: Direct loading from Upstox API URLs with gzip handling

## Installation

```bash
pip install upstox-instrument-query
```

## Usage

### Initialize the Database

From a local JSON file:

```bash
upstox-query init /path/to/instruments.json /path/to/database.db
```

From the Upstox URL:

```bash
upstox-query init https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz /path/to/database.db --url
```

### Query the Data

```python
from upstox_instrument_query import InstrumentQuery

# Initialize query interface
query = InstrumentQuery('/path/to/database.db')

# Get instrument by key
instrument = query.get_by_instrument_key('NSE_EQ|INE002A01018')
print(instrument)

# Filter by exchange
nse_instruments = query.filter_by_exchange('NSE')
print(f"Found {len(nse_instruments)} NSE instruments")

# Filter by instrument type
equity_instruments = query.filter_by_instrument_type('EQUITY')
print(f"Found {len(equity_instruments)} EQUITY instruments")

# Search by name (regex)
reliance_instruments = query.search_by_name('RELIANCE')
print(f"Found {len(reliance_instruments)} RELIANCE instruments:")
for instr in reliance_instruments[:3]:  # Print first 3
    print(f"- {instr['trading_symbol']} ({instr['instrument_type']})")

# Custom query
futures = query.custom_query('instrument_type = ? AND expiry > ?', ('FUTURES', '2025-01-01'))
print(f"Found {len(futures)} futures expiring after 2025-01-01")
```

### CLI Commands

The package provides a command-line interface for common operations:

```bash
# Initialize database from file
upstox-query init /path/to/instruments.json /path/to/database.db

# Initialize database from URL
upstox-query init https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz /path/to/database.db --url

# Update existing database from file
upstox-query update /path/to/instruments.json /path/to/database.db

# Update existing database from URL
upstox-query update https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz /path/to/database.db --url
```

## Advanced Usage

### Case-Sensitive Name Searching

```python
# Default is case-insensitive
case_insensitive = query.search_by_name('reliance')

# Enable case sensitivity
case_sensitive = query.search_by_name('RELIANCE', case_sensitive=True)
```

### Complex Custom Queries

```python
# Find all NSE futures expiring in 2025 with a lot size greater than 500
complex_query = query.custom_query(
    'exchange = ? AND instrument_type = ? AND expiry LIKE ? AND lot_size > ?',
    ('NSE', 'FUTURES', '2025-%', 500)
)
```

## Performance Notes

- **SQLite Storage**: Uses disk-based SQLite database, minimizing memory usage
- **Optimized Indexes**: Includes indexes on `instrument_key`, `exchange`, `instrument_type`, and `name` for fast queries
- **Result Caching**: Caches results for repeated queries using `lru_cache`
- **Streaming Parser**: Streams JSON parsing from both local files and URLs to handle large files efficiently
- **Compression Support**: Handles gzip-compressed JSON from URLs for direct processing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
