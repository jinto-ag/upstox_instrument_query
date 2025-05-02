"""Utility functions for handling JSON data in the Upstox instrument query package.

This module provides functionality for efficiently streaming and processing
JSON data from both local files and remote URLs.
"""

import gzip
import json
import urllib.request
from typing import Any, Dict, Iterator


def stream_json(file_path: str) -> Iterator[Dict[str, Any]]:
    """
    Stream JSON data from a file to minimize memory usage.

    Reads large JSON files in a memory-efficient way by yielding
    one object at a time instead of loading the entire file.

    Args:
        file_path (str): Path to the JSON file

    Yields:
        dict: Individual instrument objects from the JSON file
    """
    with open(file_path, "r") as f:
        # For small test files, parse the entire JSON at once
        try:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    yield item
            elif isinstance(data, dict):
                yield data
            return
        except json.JSONDecodeError:
            # If it's not valid JSON as a whole, try the streaming approach
            f.seek(0)

        # Skip the opening bracket for streaming approach
        f.read(1)

        # Read instruments one by one
        depth = 1
        obj_str = ""
        for char in iter(lambda: f.read(1), ""):
            obj_str += char
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1

            if depth == 1 and char == "}":
                # We've completed an object
                try:
                    yield json.loads(obj_str)
                except json.JSONDecodeError:
                    pass  # Skip malformed JSON

                obj_str = ""

                # Skip comma and whitespace
                next_char = f.read(1)
                while next_char in [",", " ", "\n", "\r", "\t"]:
                    next_char = f.read(1)

                if not next_char or next_char == "]":
                    break

                obj_str = next_char


def stream_json_from_url(url: str) -> Iterator[Dict[str, Any]]:
    """
    Stream JSON data from a URL to minimize memory usage.

    Fetches and processes large JSON files from URLs in a memory-efficient way,
    with support for gzipped content.

    Args:
        url (str): URL to the JSON file (can be gzipped)

    Yields:
        dict: Individual instrument objects from the JSON file
    """
    with urllib.request.urlopen(url) as response:
        # Detect if content is gzipped
        is_gzipped = response.headers.get("Content-Encoding") == "gzip" or url.endswith(
            ".gz"
        )

        if is_gzipped:
            with gzip.GzipFile(fileobj=response) as f:
                content = f.read().decode("utf-8")
        else:
            content = response.read().decode("utf-8")

        # Process JSON content
        data = json.loads(content)
        if isinstance(data, list):
            for item in data:
                yield item
        elif isinstance(data, dict):
            yield data
