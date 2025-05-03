# Upstox Instrument Query

[![PyPI version](https://img.shields.io/pypi/v/upstox-instrument-query.svg)](https://pypi.org/project/upstox-instrument-query/)
[![Python versions](https://img.shields.io/pypi/pyversions/upstox-instrument-query.svg)](https://pypi.org/project/upstox-instrument-query/)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/jinto-ag/upstox_instrument_query/blob/main/LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/jinto-ag/upstox_instrument_query)
[![Coverage 93%](https://img.shields.io/badge/coverage-73%25-yellowgreen.svg)](https://github.com/jinto-ag/upstox_instrument_query/blob/main/htmlcov/index.html)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)

A Python package to efficiently query large Upstox instruments JSON files (~60MB) using SQLite for optimal performance.

## Features

- **Memory Efficient**: Streams JSON parsing for minimal memory footprint
- **High Performance**: Uses SQLite with optimized indexes
- **Flexible**: Query by instrument key, exchange, instrument type, or custom criteria
- **Caching**: Implements LRU caching for frequently accessed queries
- **CLI Support**: Command-line tools for database initialization and updates
- **URL Support**: Direct loading from Upstox API URLs with gzip handling
- **YFinance Integration**: Look up stock details using Yahoo Finance API
- **Interactive Mode**: Interactive query interface for exploration
- **Trading Symbol Lookup**: Direct lookup by trading symbol
- **Option Chain**: Retrieve option chains for a specific ISIN
- **Advanced Filtering**: Filter by segment, ISIN, option type, and more
- **Log Management**: View, clear, archive, and manage application logs
- **Cache Management**: Clear query cache for optimal performance
- **Automated Updates**: Auto-update database with latest instrument data

## Installation

Basic installation:

```bash
pip install upstox-instrument-query
```

With YFinance support:

```bash
pip install "upstox-instrument-query[yfinance]"
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
equity_instruments = query.filter_by_instrument_type('EQ')
print(f"Found {len(equity_instruments)} EQUITY instruments")

# Search by name (regex)
reliance_instruments = query.search_by_name('RELIANCE')
print(f"Found {len(reliance_instruments)} RELIANCE instruments:")
for instr in reliance_instruments[:3]:  # Print first 3
    print(f"- {instr['trading_symbol']} ({instr['instrument_type']})")

# Custom query
futures = query.custom_query('instrument_type = ? AND expiry > ?', ('FUTURES', '2025-01-01'))
print(f"Found {len(futures)} futures expiring after 2025-01-01")

# Get by trading symbol
reliance = query.get_by_trading_symbol('RELIANCE')
print(f"Found RELIANCE with key: {reliance['instrument_key']}")

# Filter by segment
nse_fo = query.filter_by_segment('NSE_FO')
print(f"Found {len(nse_fo)} NSE F&O instruments")

# Filter by ISIN
hdfc_instruments = query.filter_by_isin('INE001A01036')
print(f"Found {len(hdfc_instruments)} instruments with ISIN INE001A01036")

# Filter by option type
call_options = query.filter_by_option_type('CE')
print(f"Found {len(call_options)} call options")

# Get option chain
reliance_options = query.get_option_chain('INE002A01018', expiry='2025-05-29')
print(f"Found {len(reliance_options)} options in the chain for expiry 2025-05-29")
```

### Yahoo Finance Integration

```python
from upstox_instrument_query import InstrumentQuery
from upstox_instrument_query.yfinance import get_ticker_info, find_corresponding_instrument, display_ticker_info, display_corresponding_instruments

# Initialize query interface
query = InstrumentQuery('/path/to/database.db')

# Get information about a stock from Yahoo Finance
ticker_info = get_ticker_info('MSFT')  # Microsoft

# Display the ticker information
display_ticker_info(ticker_info)

# Find corresponding instruments in Upstox database
matching_instruments = find_corresponding_instrument(query, ticker_info)

# Display the matching instruments
display_corresponding_instruments(matching_instruments)
```

### Interactive Mode

The package provides an interactive shell for exploring the database:

```bash
# Start interactive mode
upstox-query interactive /path/to/database.db
```

In interactive mode, you can run commands like:

```bash
> help                           # Show available commands
> exchanges                      # List all exchanges
> types                          # List all instrument types
> segments                       # List all segments
> search RELIANCE                # Search for instruments containing "RELIANCE"
> filter NSE EQ                  # Filter by exchange and instrument type
> filter NSE_FO                  # Filter by segment
> isin INE001A01036              # Search by ISIN
> ticker MSFT                    # Look up Yahoo Finance ticker
> symbol RELIANCE                # Look up by trading symbol
> option_chain INE002A01018      # Get option chain for Reliance
> custom instrument_type = 'FUTURES' AND expiry > '2025-01-01'  # Custom SQL query
> exit                           # Exit interactive mode
```

### CLI Commands

The package provides a comprehensive command-line interface:

```bash
# Database Management
upstox-query init                        # Initialize from default URL
upstox-query init /path/to/instruments.json     # Initialize from file
upstox-query init https://custom-url.com/data.json --url  # Initialize from custom URL
upstox-query update                      # Update from default URL

# Basic Querying (short form: upstox-query q)
upstox-query query -k 'NSE_EQ|INE002A01018'    # Query by instrument key
upstox-query query -e NSE                      # Query by exchange
upstox-query query -t EQ                       # Query by instrument type
upstox-query query -s NSE_FO                   # Query by segment
upstox-query query -i INE001A01036             # Query by ISIN
upstox-query query -o CE                       # Query by option type (CE/PE)
upstox-query query -n "RELIANCE"               # Search by name (regex)
upstox-query query -y RELIANCE                 # Query by trading symbol
upstox-query query -c INE002A01018             # Get option chain for ISIN
upstox-query query -w "name LIKE ?" -p "%BANK%"  # Custom SQL query
upstox-query query -n "RELIANCE" --json        # Output in JSON format
upstox-query query -c INE002A01018 --expiry 2025-05-29  # Option chain with expiry

# Yahoo Finance (short form: upstox-query t)
upstox-query ticker MSFT                       # Get Yahoo Finance data
upstox-query ticker RELIANCE.NS --find-instruments  # Show related instruments

# Interactive Mode (short form: upstox-query i)
upstox-query interactive                       # Start interactive mode

# Log Management
upstox-query logs --list                       # List available log files
upstox-query logs --view                       # View main log contents
upstox-query logs --view --tail 20             # View last 20 lines of main log
upstox-query logs --view --search ERROR        # View only lines with 'ERROR'
upstox-query logs --view --log-name database   # View database-specific logs
upstox-query logs --clear                      # Clear all logs
upstox-query logs --archive                    # Archive logs to a zip file
upstox-query logs --clean-archives --days 15   # Remove archives older than 15 days

# Cache Management
upstox-query cache                             # Clear query cache
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

# Find all Nifty Bank options expiring next month
from datetime import datetime
next_month = (datetime.now().month % 12) + 1
year = datetime.now().year + (1 if next_month < datetime.now().month else 0)
expiry_pattern = f"{year}-{next_month:02d}-%"

nifty_bank_options = query.custom_query(
    'name LIKE ? AND instrument_type IN (?, ?) AND expiry LIKE ?',
    ('BANKNIFTY%', 'CE', 'PE', expiry_pattern)
)
```

### Log Management

The package provides comprehensive logging facilities:

```python
# Import log management functions
from upstox_instrument_query.logging_config import (
    get_logger, view_logs, clear_logs, archive_logs, clean_old_archives
)

# Create a logger for your application
logger = get_logger("my_app")
logger.info("This is an informational message")
logger.warning("This is a warning message")
logger.error("This is an error message")

# View log contents
log_lines = view_logs(log_name="main", tail=20)
for line in log_lines:
    print(line)

# Clear logs
clear_logs()

# Archive logs to a zip file
archive_path = archive_logs()
print(f"Logs archived to {archive_path}")

# Clean up old archives
removed_files = clean_old_archives(days=30)
print(f"Removed {len(removed_files)} old archive files")
```

### Cache Management

The package implements LRU caching for query results, which can be managed programmatically:

```python
from upstox_instrument_query import InstrumentQuery

query = InstrumentQuery('/path/to/database.db')

# Clear the query cache
query.clear_cache()
```

## Performance Notes

- **SQLite Storage**: Uses disk-based SQLite database, minimizing memory usage
- **Optimized Indexes**: Includes indexes on `instrument_key`, `exchange`, `instrument_type`, and `name` for fast queries
- **Result Caching**: Caches results for repeated queries using `lru_cache`
- **Streaming Parser**: Streams JSON parsing from both local files and URLs to handle large files efficiently
- **Compression Support**: Handles gzip-compressed JSON from URLs for direct processing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/jinto-ag/upstox_instrument_query.git
   cd upstox_instrument_query
   ```

2. Install development dependencies:

   ```bash
   pip install -e ".[dev]"
   # or
   pip install -e . pytest pytest-cov pre-commit
   ```

3. Install pre-commit hooks:

   ```bash
   pre-commit install --hook-type pre-commit --hook-type commit-msg
   ```

### Running Tests

Run the test suite using pytest:

```bash
pytest
```

To generate a coverage report:

```bash
pytest --cov=upstox_instrument_query --cov-report=html
```

The coverage report will be available in the `htmlcov` directory. Open `htmlcov/index.html` in your browser to view it.

### Automated Version Management

This project uses GitHub Actions to automatically bump versions and generate changelogs based on conventional commit messages when merging to the main branch:

- `feat:` commits trigger a minor version bump
- `feat!:`, `fix!:`, or commits with `BREAKING CHANGE` trigger a major version bump
- All other commits trigger a patch version bump

The CI process will:

1. Detect the appropriate version bump from commits
2. Update version numbers in all relevant files
3. Generate changelog entries
4. Create GitHub releases automatically

For manual releases, you can also use the workflow dispatch:

```bash
# From GitHub Actions UI, manually trigger the 'Release with Changelog' workflow
```

### Test-Driven Development (TDD)

This project follows Test-Driven Development practices for all new features. When contributing or adding new functionality, please follow these TDD principles:

1. **Write tests first**: Before implementing any new feature, write tests that define the expected behavior
2. **Run the tests**: Verify that the tests fail (since the feature doesn't exist yet)
3. **Implement the feature**: Write the minimal code needed to make the tests pass
4. **Refactor**: Clean up the code while ensuring tests continue to pass
5. **Repeat**: Continue this cycle for each new piece of functionality

Example TDD workflow:

```bash
# 1. Create a test file for the new feature
touch tests/test_new_feature.py

# 2. Write tests for the expected behavior
# Edit tests/test_new_feature.py with test cases

# 3. Run tests to verify they fail appropriately
pytest tests/test_new_feature.py -v

# 4. Implement the feature
# Edit the relevant files in upstox_instrument_query/

# 5. Run tests again to see if they pass
pytest tests/test_new_feature.py -v

# 6. Run coverage to ensure proper test coverage
pytest --cov=upstox_instrument_query --cov-report=term-missing
```

Always aim to maintain high test coverage (90%+) when adding new features. The project CI pipeline will automatically check test coverage on pull requests.

### Conventional Commits

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages. This leads to more readable messages that are easy to follow when looking through the project history.

Commit messages should be structured as follows:

```txt
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types include:

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools

Examples:

```txt
feat: add option chain retrieval functionality
fix: correct database connection leak
docs: update README with new API methods
```

The pre-commit hooks enforce this convention when committing changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
