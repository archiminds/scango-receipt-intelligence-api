import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any, Union
from app.models.schemas import ParsedItem


class Normalizer:
    """Normalizes extracted receipt data."""

    @staticmethod
    def normalize_date(date_str: Optional[str]) -> Optional[str]:
        """Normalize date string to ISO format YYYY-MM-DD."""
        if not date_str:
            return None

        cleaned = date_str.strip()
        # Remove common prefixes
        cleaned = re.sub(r'(?i)(receipt|invoice)?\s*date[:\-]?', '', cleaned).strip()
        cleaned = cleaned.replace(',', ' ')
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Strip any trailing time component (e.g., 2026-04-10 09:12)
        time_match = re.search(r'((?:\d{4}|\d{1,2})[/-]\d{1,2}[/-](?:\d{4}|\d{2}))[\sT]+\d{1,2}:\d{2}(?::\d{2})?', cleaned)
        if time_match:
            cleaned = time_match.group(1)

        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y.%m.%d",
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d %b %Y",
            "%d %B %Y",
            "%b %d %Y",
            "%B %d %Y",
        ]

        for fmt in formats:
            try:
                date_obj = datetime.strptime(cleaned, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue

        # Attempt to pull date fragments if additional text remains
        fragment_patterns = [
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4}',
            r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}',
        ]

        for pattern in fragment_patterns:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                return Normalizer.normalize_date(match.group(0))

        return None

    @staticmethod
    def extract_date_from_text(text: Optional[str]) -> Optional[str]:
        """Pull the first recognizable date from free-form text."""
        if not text:
            return None

        patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            r'\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4}\b'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                normalized = Normalizer.normalize_date(match.group(0))
                if normalized:
                    return normalized
        return None

    @staticmethod
    def normalize_amount(amount_str: Optional[Union[str, float, int, Decimal]]) -> Optional[Decimal]:
        """Normalize amount string or number to Decimal."""
        if amount_str is None:
            return None

        # If already Decimal, just quantize
        if isinstance(amount_str, Decimal):
            return amount_str.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Convert to string if it's a number
        if isinstance(amount_str, (float, int)):
            amount_str = str(amount_str)

        # Remove currency symbols and extra spaces
        cleaned = re.sub(r'[^\d\.,-]', '', amount_str.strip())

        # Handle different decimal separators
        if ',' in cleaned and '.' in cleaned:
            # European format: 1.234,56
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # US format: 1,234.56
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Could be decimal or thousands separator
            if len(cleaned.split(',')[1]) <= 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')

        try:
            return Decimal(cleaned).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except:
            return None

    @staticmethod
    def normalize_vendor(vendor_str: Optional[str]) -> Optional[str]:
        """Normalize vendor name."""
        if not vendor_str:
            return None

        # Clean and title case
        cleaned = re.sub(r'[^\w\s]', '', vendor_str.strip())
        return cleaned.title() if cleaned else None

    @staticmethod
    def normalize_items(items_data: List[Dict[str, Any]]) -> List[ParsedItem]:
        """Normalize items list."""
        normalized_items = []

        for item in items_data:
            try:
                if isinstance(item, ParsedItem):
                    item_data = item.dict()
                else:
                    item_data = item

                raw_quantity = item_data.get('quantity', 1) or 1
                quantity = max(1, int(raw_quantity))
                unit_price = Normalizer.normalize_amount(item_data.get('unit_price'))
                total_price = Normalizer.normalize_amount(item_data.get('total_price'))

                if total_price is None and unit_price is not None:
                    total_price = (unit_price * Decimal(quantity)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                elif unit_price is None and total_price is not None:
                    unit_price = (total_price / Decimal(quantity)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                normalized_item = ParsedItem(
                    name=(item_data.get('name') or '').strip(),
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
                if normalized_item.name:
                    normalized_items.append(normalized_item)
            except (ValueError, TypeError):
                continue

        return normalized_items

    @staticmethod
    def compute_gst(total_amount: Optional[Decimal], existing_gst: Optional[Decimal]) -> Decimal:
        """Compute GST using Australian logic if not present."""
        if existing_gst is not None:
            return existing_gst

        if total_amount is None:
            return Decimal('0.00')

        # Australian GST: GST = total * (10/110)
        gst_rate = Decimal('10') / Decimal('110')
        gst = (total_amount * gst_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return gst
