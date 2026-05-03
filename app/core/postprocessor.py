"""Final response helpers.

Postprocessing owns request IDs, cache hashes, and final confidence scoring so
the service can keep its main workflow readable.
"""

import hashlib
import uuid
from typing import Optional
from app.models.schemas import ReceiptParseResponse


class Postprocessor:
    """Handles final processing of receipt parsing results."""

    @staticmethod
    def generate_request_id() -> str:
        """Generate a unique request ID."""
        return str(uuid.uuid4())

    @staticmethod
    def hash_text(text: str) -> str:
        """Generate SHA-256 hash of normalized text for caching."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    @staticmethod
    def calculate_confidence_score(response: ReceiptParseResponse) -> float:
        """Calculate overall confidence score based on various factors."""
        confidence = 0.0
        factors = 0

        # The score is a weighted heuristic over extracted fields. It is not a
        # model probability; it is a practical signal for downstream consumers.
        # Vendor confidence
        if response.vendor:
            confidence += 0.8
        factors += 1

        # Date confidence
        if response.receipt_date:
            confidence += 0.9
        factors += 1

        # Amount confidence
        if response.total_amount is not None:
            confidence += 0.95
        factors += 1

        if response.gst_amount is not None:
            confidence += 0.9
        factors += 1

        # Items confidence
        if response.items:
            item_confidence = min(len(response.items) * 0.1, 0.8)
            confidence += item_confidence
        factors += 1

        # Categorization confidence
        confidence += response.confidence_score
        factors += 1

        return confidence / factors if factors > 0 else 0.0

    @staticmethod
    def finalize_response(response: ReceiptParseResponse,
                         request_id: str,
                         cache_status: str,
                         warnings: list) -> ReceiptParseResponse:
        """Finalize the response with calculated fields."""
        # Update confidence score after validation because warnings may reflect
        # fields that reduce trust in the result.
        response.confidence_score = Postprocessor.calculate_confidence_score(response)

        # Set cache status and request ID
        response.cache_status = cache_status
        response.request_id = request_id
        response.warnings = warnings

        return response
