"""Tests for the utility functions module.

This module tests the JSON streaming utilities for handling both
local files and remote URLs.
"""

import os
import tempfile
from unittest import mock

from upstox_instrument_query.utils import stream_json, stream_json_from_url


def test_stream_json(sample_json_path):
    """Test streaming JSON data from a file."""
    count = 0
    for instrument in stream_json(sample_json_path):
        count += 1
        assert isinstance(instrument, dict)
        assert "instrument_key" in instrument
        assert "exchange" in instrument
        assert "instrument_type" in instrument
        assert "name" in instrument

    assert count == 5


def test_stream_json_handles_malformed_json():
    """Test that stream_json can handle malformed JSON."""

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write('[{"valid": true}, {invalid json}, {"valid": true}]')
        temp_file = f.name

    try:
        count = 0
        for item in stream_json(temp_file):
            count += 1
            assert item["valid"] is True

        assert count == 1
    finally:
        os.unlink(temp_file)


def test_stream_json_empty_file():
    """Test streaming from an empty JSON file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("[]")
        temp_file = f.name

    try:
        items = list(stream_json(temp_file))
        assert len(items) == 0
    finally:
        os.unlink(temp_file)


def test_stream_json_end_of_file():
    """Test handling the end of file condition in streaming."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:

        f.write('[{"test": "value"}]')
        temp_file = f.name

    try:
        items = list(stream_json(temp_file))
        assert len(items) == 1
        assert items[0]["test"] == "value"
    finally:
        os.unlink(temp_file)


def test_stream_json_malformed_streaming():
    """Test handling malformed JSON in the streaming mode."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:

        f.write('[{"valid": true}, {"missing": "closing_brace"')
        temp_file = f.name

    try:
        items = list(stream_json(temp_file))
        assert len(items) == 1
        assert items[0]["valid"] is True
    finally:
        os.unlink(temp_file)


def test_stream_json_skip_comma():
    """Test handling of the comma and
    whitespace skipping in the streaming approach.
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:

        f.write('[{"key1": "value1"},\n\t {"key2": "value2"},  {"key3": "value3"}]')
        temp_file = f.name

    try:
        items = list(stream_json(temp_file))
        assert len(items) == 3
        assert items[0]["key1"] == "value1"
        assert items[1]["key2"] == "value2"
        assert items[2]["key3"] == "value3"
    finally:
        os.unlink(temp_file)


def test_stream_json_complex_edge_cases():
    """Test various edge cases in the JSON streaming functionality."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:

        f.write(
            """[
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2",}
        ]"""
        )
        temp_file = f.name

    try:

        items = list(stream_json(temp_file))
        assert len(items) > 0
    finally:
        os.unlink(temp_file)


def test_stream_json_whitespace_handling():
    """Test specific whitespace handling in JSON streaming."""

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:

        f.write('[{"id": 1},\n\r\t \n{"id": 2}]')
        temp_file = f.name

    try:
        results = list(stream_json(temp_file))
        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2
    finally:
        os.unlink(temp_file)


@mock.patch("urllib.request.urlopen")
def test_stream_json_from_url_uncompressed(mock_urlopen):
    """Test streaming JSON data from a URL."""

    mock_response = mock.MagicMock()
    mock_response.headers = {}
    mock_response.read.return_value = (
        b'[{"instrument_key": "TEST1"}, {"instrument_key": "TEST2"}]'
    )
    mock_urlopen.return_value.__enter__.return_value = mock_response

    count = 0
    for instrument in stream_json_from_url("http://example.com/data.json"):
        count += 1
        assert "instrument_key" in instrument

    assert count == 2
    mock_urlopen.assert_called_once_with("http://example.com/data.json")


@mock.patch("upstox_instrument_query.utils.gzip.GzipFile")
@mock.patch("urllib.request.urlopen")
def test_stream_json_from_url_gzipped(mock_urlopen, mock_gzip):
    """Test streaming gzipped JSON data from a URL."""

    mock_gzip_instance = mock.MagicMock()
    mock_gzip_instance.read.return_value = (
        b'[{"instrument_key": "TEST1"}, {"instrument_key": "TEST2"}]'
    )
    mock_gzip.return_value.__enter__.return_value = mock_gzip_instance

    mock_response = mock.MagicMock()
    mock_response.headers = {"Content-Encoding": "gzip"}
    mock_urlopen.return_value.__enter__.return_value = mock_response

    count = 0
    for instrument in stream_json_from_url("http://example.com/data.json.gz"):
        count += 1
        assert "instrument_key" in instrument

    assert count == 2
    mock_urlopen.assert_called_once_with("http://example.com/data.json.gz")
    mock_gzip.assert_called_once()


@mock.patch("urllib.request.urlopen")
def test_stream_json_from_url_dict_response(mock_urlopen):
    """Test handling a dict response instead of a list."""

    mock_response = mock.MagicMock()
    mock_response.headers = {}
    mock_response.read.return_value = b'{"instrument_key": "TEST1", "name": "Test"}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    count = 0
    for instrument in stream_json_from_url("http://example.com/data.json"):
        count += 1
        assert instrument["instrument_key"] == "TEST1"
        assert instrument["name"] == "Test"

    assert count == 1
    mock_urlopen.assert_called_once_with("http://example.com/data.json")


@mock.patch("upstox_instrument_query.utils.gzip.GzipFile")
@mock.patch("urllib.request.urlopen")
def test_stream_json_from_url_with_gz_extension(mock_urlopen, mock_gzip):
    """Test streaming from URL with .gz extension."""

    mock_gzip_instance = mock.MagicMock()
    mock_gzip_instance.read.return_value = b'[{"instrument_key": "TEST1"}]'
    mock_gzip.return_value.__enter__.return_value = mock_gzip_instance

    mock_response = mock.MagicMock()
    mock_response.headers = {}
    mock_urlopen.return_value.__enter__.return_value = mock_response

    items = list(stream_json_from_url("http://example.com/data.json.gz"))
    assert len(items) == 1
    assert items[0]["instrument_key"] == "TEST1"

    mock_gzip.assert_called_once()


@mock.patch("urllib.request.urlopen")
def test_stream_json_from_url_empty_list(mock_urlopen):
    """Test streaming an empty list from URL."""

    mock_response = mock.MagicMock()
    mock_response.headers = {}
    mock_response.read.return_value = b"[]"
    mock_urlopen.return_value.__enter__.return_value = mock_response

    count = 0
    for _ in stream_json_from_url("http://example.com/data.json"):
        count += 1

    assert count == 0
