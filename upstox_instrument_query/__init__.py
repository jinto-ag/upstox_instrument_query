"""Upstox Instrument Query.

A Python package to efficiently query large Upstox instruments JSON files
using SQLite for optimal performance.
"""

# Only explicitly export what's needed in the public API
from .query import InstrumentQuery  # noqa: F401

__version__ = "0.1.0"
__author__ = "Jinto A G"
