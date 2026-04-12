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

        # Common date patterns
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD
            r'(\d{1,2})\s+(\w{3})\s+(\d{4})',      # DD Mon YYYY
        ]

        for pattern in patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 3:
                        parts = [int(g) for g in match.groups()]
                        # Assume DD/MM/YYYY for ambiguous formats
                        if parts[2] > 31:  # Year first
                            year, month, day = parts
                        elif parts[0] > 12:  # Day first
                            day, month, year = parts
                        else:  # Assume DD/MM/YYYY
                            day, month, year = parts

                        date_obj = datetime(year, month, day)
                        return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue

        return None

    @staticmethod
    def normalize_amount(amount_str: Optional[Union[str, float, int]]) -> Optional[Decimal]:
        """Normalize amount string or number to Decimal."""
        if amount_str is None:
            return None

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
                normalized_item = ParsedItem(
                    name=item.get('name', '').strip(),
                    quantity=int(item.get('quantity', 1)),
                    unit_price=Normalizer.normalize_amount(item.get('unit_price')),
                    total_price=Normalizer.normalize_amount(item.get('total_price'))
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