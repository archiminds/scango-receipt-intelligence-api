"""Unit tests for text preprocessing behavior.

These tests protect the cache-key and parser-input normalization assumptions
used by ReceiptService.
"""

import pytest
from app.core.preprocessor import Preprocessor


class TestPreprocessor:
    """Unit tests for Preprocessor class."""

    def test_clean_text_basic(self):
        """Test basic text cleaning."""
        text = "  Hello   World!  "
        result = Preprocessor.clean_text(text)
        assert result == "Hello World!"

    def test_clean_text_special_chars(self):
        """Test cleaning with special characters."""
        text = "Total: $10.50\nGST: $1.05"
        result = Preprocessor.clean_text(text)
        assert "Total:" in result
        assert "GST:" in result

    def test_normalize_text(self):
        """Test text normalization."""
        text = "  Hello   WORLD!  "
        result = Preprocessor.normalize_text(text)
        assert result == "hello world"

    def test_extract_currency_aud(self):
        """Test AUD currency extraction."""
        text = "Total: $45.67"
        result = Preprocessor.extract_currency(text)
        assert result == "AUD"

    def test_extract_currency_eur(self):
        """Test EUR currency extraction."""
        text = "Total: €45.67"
        result = Preprocessor.extract_currency(text)
        assert result == "EUR"

    def test_extract_currency_none(self):
        """Test no currency found."""
        text = "Total: 45.67"
        result = Preprocessor.extract_currency(text)
        assert result is None
