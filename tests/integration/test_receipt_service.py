import pytest
import json
from app.services.receipt_service import ReceiptService
from app.models.schemas import ReceiptParseRequest


class TestReceiptServiceIntegration:
    """Integration tests for ReceiptService."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return ReceiptService()

    def test_parse_receipt_basic(self, service):
        """Test basic receipt parsing."""
        request = ReceiptParseRequest(
            receipt_text="STARBUCKS\nTotal: $5.50\nGST: $0.50",
            currency="AUD"
        )

        # Mock the Bedrock client to avoid actual API calls
        service.bedrock_client.parse_receipt = lambda x: None  # Return None to test fallback

        response = service.parse_receipt(request)

        assert response.request_id is not None
        assert response.cache_status == "miss"
        assert response.currency == "AUD"
        assert isinstance(response.warnings, list)

    def test_parse_receipt_with_gst_computation(self, service):
        """Test GST computation when missing."""
        request = ReceiptParseRequest(
            receipt_text="COFFEE SHOP\nTotal: $11.00",
            currency="AUD"
        )

        # Mock Bedrock to return data without GST
        mock_response = type('MockResponse', (), {
            'vendor': 'COFFEE SHOP',
            'receipt_date': None,
            'items': [{'name': 'Coffee', 'quantity': 1, 'unit_price': 10.0, 'total_price': 10.0}],
            'subtotal_amount': 10.0,
            'total_amount': 11.0,
            'gst_amount': None,
            'currency': 'AUD'
        })()
        service.bedrock_client.parse_receipt = lambda x: mock_response

        response = service.parse_receipt(request)

        # GST should be computed: 11.00 * (10/110) = 1.00
        assert response.gst_amount == 1.00
        assert response.total_amount == 11.0

    def test_parse_receipt_validation(self, service):
        """Test request validation."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="receipt_text cannot be empty"):
            request = ReceiptParseRequest(receipt_text="", currency="AUD")
            service.parse_receipt(request)

    def test_parse_receipt_caching(self, service):
        """Test caching behavior."""
        request = ReceiptParseRequest(
            receipt_text="TEST RECEIPT\nTotal: $10.00",
            currency="AUD"
        )

        # Mock Bedrock to return data
        mock_response = type('MockResponse', (), {
            'vendor': 'TEST VENDOR',
            'receipt_date': None,
            'items': [{'name': 'Test Item', 'quantity': 1, 'unit_price': 10.0, 'total_price': 10.0}],
            'subtotal_amount': 10.0,
            'total_amount': 10.0,
            'gst_amount': None,
            'currency': 'AUD'
        })()
        service.bedrock_client.parse_receipt = lambda x: mock_response

        # First call
        response1 = service.parse_receipt(request)
        assert response1.cache_status == "miss"

        # Second call with same text should hit cache (if implemented)
        # Note: Cache implementation is TODO, so this will always miss
        response2 = service.parse_receipt(request)
        assert response2.cache_status == "miss"