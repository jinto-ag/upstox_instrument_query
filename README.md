# Upstox Instrument Query

[![PyPI version](https://img.shields.io/pypi/v/upstox-instrument-query.svg)](https://pypi.org/project/upstox-instrument-query/)
[![Python versions](https://img.shields.io/pypi/pyversions/upstox-instrument-query.svg)](https://pypi.org/project/upstox-instrument-query/)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/jinto-ag/upstox_instrument_query/blob/main/LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/jinto-ag/upstox_instrument_query)
[![Coverage 93%](https://img.shields.io/badge/coverage-93%25-brightgreen.svg)](https://github.com/jinto-ag/upstox_instrument_query/blob/main/htmlcov/index.html)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)

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
