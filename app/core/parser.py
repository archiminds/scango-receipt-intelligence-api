"""Deterministic fallback parser.

This parser extracts only high-value fields with regex patterns when Bedrock is
unavailable or returns invalid output. It is intentionally conservative so it
does not invent detailed item data from weak signals.
"""

from typing import Optional
from app.models.schemas import BedrockParseResponse, ParsedItem
from app.core.normalizer import Normalizer


class Parser:
    """Parses and structures receipt data from various sources."""

    @staticmethod
    def parse_bedrock_response(bedrock_response: BedrockParseResponse) -> dict:
        """Parse Bedrock response into normalized structure."""
        return {
            'vendor': Normalizer.normalize_vendor(bedrock_response.vendor),
            'receipt_date': Normalizer.normalize_date(bedrock_response.receipt_date),
            'items': Normalizer.normalize_items(bedrock_response.items),
            'subtotal_amount': bedrock_response.subtotal_amount,
            'total_amount': bedrock_response.total_amount,
            'gst_amount': bedrock_response.gst_amount,
            'currency': bedrock_response.currency
        }

    @staticmethod
    def extract_key_fields(text: str) -> dict:
        """Extract key fields from raw receipt text using regex patterns."""
        import re

        fields = {}

        # Vendor patterns prefer obvious receipt header or "from/at" phrases.
        vendor_patterns = [
            r'(?:from|at)\s+([A-Z][a-zA-Z\s]+)',
            r'^([A-Z][A-Z\s]+)\n',
            r'([A-Z][a-zA-Z\s]+)\s+(?:receipt|invoice)'
        ]

        for pattern in vendor_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                fields['vendor'] = match.group(1).strip()
                break

        # Date patterns cover common numeric and month-name formats before
        # delegating final normalization to Normalizer.
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields['receipt_date'] = Normalizer.normalize_date(match.group(0))
                break

        # Amount patterns focus on explicit totals because line-item extraction
        # without AI is much less reliable.
        amount_patterns = [
            r'total\s*[\$:]\s*([\d\.,]+)',
            r'amount\s*[\$:]\s*([\d\.,]+)',
            r'[\$]\s*([\d\.,]+)\s*(?:total|due|pay)'
        ]

        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields['total_amount'] = Normalizer.normalize_amount(match.group(1))
                break

        return fields
