"""Tests for edge cases in the utils module.

This module contains targeted tests for the precise edge cases
that are difficult to reach in normal testing.
"""

import os
import tempfile
from unittest import mock


class TestUtilsEdgeCases:
    """Very specific tests to hit hard-to-reach code paths."""

    def test_stream_json_complex_whitespace(self):
        """Test skipping complex whitespace combinations (line 57)."""
        from upstox_instrument_query.utils import stream_json

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write('[{"id": 1}, \n\r\t {"id": 2}]')
            temp_file = f.name

        try:
            results = list(stream_json(temp_file))
            assert len(results) == 2
            assert results[0]["id"] == 1
            assert results[1]["id"] == 2
        finally:
            os.unlink(temp_file)

    def test_stream_json_from_url_dict_response(self):
        """Test handling a dictionary response from URL (line 68)."""
        from upstox_instrument_query.utils import stream_json_from_url

        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = mock.MagicMock()
            mock_response.headers = {}
            mock_response.read.return_value = (
                b'{"key": "value", "nested": {"data": true}}'
            )
            mock_urlopen.return_value.__enter__.return_value = mock_response

            results = list(stream_json_from_url("http://example.com/api"))

            assert len(results) == 1
            assert results[0]["key"] == "value"
            assert results[0]["nested"]["data"] is True
