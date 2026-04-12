import re
from typing import Optional


class Preprocessor:
    """Handles cleaning and normalization of OCR-extracted receipt text."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean OCR text by removing noise and normalizing whitespace."""
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove common OCR artifacts
        text = re.sub(r'[|]', ' ', text)  # Remove vertical bars
        text = re.sub(r'[_]{2,}', ' ', text)  # Remove underscores

        # Normalize line breaks
        text = re.sub(r'\n+', '\n', text)

        return text.strip()

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for consistent hashing and processing."""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove punctuation except essential ones
        text = re.sub(r'[^\w\s\.\,\$]', '', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        return text

    @staticmethod
    def extract_currency(text: str) -> Optional[str]:
        """Extract currency indicators from text."""
        # Look for common currency symbols
        if '$' in text:
            return 'AUD'  # Default to AUD for Australian context
        if '€' in text:
            return 'EUR'
        if '£' in text:
            return 'GBP'
        if '¥' in text:
            return 'JPY'

        return None