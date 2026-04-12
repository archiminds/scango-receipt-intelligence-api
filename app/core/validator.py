from typing import List
from decimal import Decimal
from app.models.schemas import ReceiptParseResponse, ParsedItem


class Validator:
    """Validates receipt parsing results."""

    @staticmethod
    def validate_response(response: ReceiptParseResponse) -> List[str]:
        """Validate the complete response and return list of warnings."""
        warnings = []

        # Check required fields
        if not response.category:
            warnings.append("Category is missing")

        if response.confidence_score < 0 or response.confidence_score > 1:
            warnings.append("Confidence score out of valid range [0,1]")

        # Validate amounts
        warnings.extend(Validator._validate_amounts(response))

        # Validate items
        warnings.extend(Validator._validate_items(response.items))

        # Validate GST
        if response.gst_amount is None:
            warnings.append("GST amount is missing")
        elif response.gst_amount < 0:
            warnings.append("GST amount is negative")

        # Validate currency
        if not response.currency:
            warnings.append("Currency is missing")

        return warnings

    @staticmethod
    def _validate_amounts(response: ReceiptParseResponse) -> List[str]:
        """Validate monetary amounts."""
        warnings = []

        if response.total_amount is None:
            warnings.append("Total amount is missing")
            return warnings

        if response.total_amount < 0:
            warnings.append("Total amount is negative")

        if response.subtotal_amount is not None:
            if response.subtotal_amount < 0:
                warnings.append("Subtotal amount is negative")
            elif response.subtotal_amount > response.total_amount:
                warnings.append("Subtotal amount exceeds total amount")

        if response.gst_amount is not None and response.subtotal_amount is not None:
            expected_total = response.subtotal_amount + response.gst_amount
            if abs(expected_total - response.total_amount) > Decimal('0.01'):
                warnings.append("GST + subtotal doesn't match total amount")

        return warnings

    @staticmethod
    def _validate_items(items: List[ParsedItem]) -> List[str]:
        """Validate parsed items."""
        warnings = []

        if not items:
            warnings.append("No items found in receipt")
            return warnings

        for i, item in enumerate(items):
            if not item.name.strip():
                warnings.append(f"Item {i+1} has no name")

            if item.quantity is not None and item.quantity <= 0:
                warnings.append(f"Item {i+1} has invalid quantity: {item.quantity}")

            if item.unit_price is not None and item.unit_price < 0:
                warnings.append(f"Item {i+1} has negative unit price")

            if item.total_price is not None and item.total_price < 0:
                warnings.append(f"Item {i+1} has negative total price")

            # Check if unit_price * quantity ≈ total_price
            if (item.unit_price is not None and item.quantity is not None
                and item.total_price is not None):
                expected_total = item.unit_price * item.quantity
                if abs(expected_total - item.total_price) > Decimal('0.01'):
                    warnings.append(f"Item {i+1} price calculation doesn't match")

        return warnings

    @staticmethod
    def is_response_valid(response: ReceiptParseResponse) -> bool:
        """Check if response is valid (no critical errors)."""
        warnings = Validator.validate_response(response)

        # Define critical warnings that make response invalid
        critical_warnings = [
            "Category is missing",
            "Total amount is missing",
            "GST amount is missing"
        ]

        return not any(warning in warnings for warning in critical_warnings)