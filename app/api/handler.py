import json
import logging
import os
from typing import Dict, Any, Optional
from app.services.receipt_service import ReceiptService
from app.models.schemas import ReceiptParseRequest, ReceiptParseResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instance - can be overridden for testing
_receipt_service: Optional[ReceiptService] = None


def get_receipt_service() -> ReceiptService:
    """Get or create receipt service instance."""
    global _receipt_service
    if _receipt_service is None:
        _receipt_service = ReceiptService()
    return _receipt_service


def set_receipt_service(service: ReceiptService):
    """Set receipt service instance (for testing)."""
    global _receipt_service
    _receipt_service = service


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler for receipt parsing API."""
    try:
        logger.info("Received API Gateway event")

        http_method, path = _extract_method_and_path(event)

        # Parse request
        if http_method == 'POST' and path == '/v1/receipts/parse':
            return _handle_parse_request(event)
        else:
            return _create_response(404, {"error": "Not Found"})

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return _create_response(500, {"error": "Internal Server Error"})


def _handle_parse_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST /v1/receipts/parse request."""
    try:
        # Parse request body
        body = event.get('body', '{}')
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')

        request_data = json.loads(body)

        # Validate and create request object
        parse_request = ReceiptParseRequest(**request_data)

        # Get service and process the request
        service = get_receipt_service()
        response = service.parse_receipt(parse_request)

        return _create_response(200, response.model_dump())

    except json.JSONDecodeError:
        return _create_response(400, {"error": "Invalid JSON in request body"})
    except ValueError as e:
        return _create_response(400, {"error": str(e)})
    except Exception as e:
        logger.error(f"Error processing parse request: {str(e)}", exc_info=True)
        return _create_response(500, {"error": "Failed to process receipt"})


def _extract_method_and_path(event: Dict[str, Any]) -> (Optional[str], Optional[str]):
    """
    Extract HTTP method and path supporting both REST API (v1) and HTTP API (v2) payload formats.
    """
    method = event.get('httpMethod')
    path = event.get('path')

    if not method or not path:
        request_context = event.get('requestContext', {})
        http_meta = request_context.get('http', {})

        method = method or http_meta.get('method')
        path = path or http_meta.get('path') or event.get('rawPath')

    if path and request_context := event.get('requestContext', {}):
        stage = request_context.get('stage')
        if stage and path.startswith(f"/{stage}"):
            # Strip stage prefix so routing works consistently
            path = path[len(stage) + 1 :] if path != f"/{stage}" else "/"

    return method, path


def _create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
        },
        "body": json.dumps(body, default=str)  # Handle Decimal serialization
    }


# For local testing
if __name__ == "__main__":
    # Sample test event
    test_event = {
        "httpMethod": "POST",
        "path": "/v1/receipts/parse",
        "body": json.dumps({
            "receipt_text": "STARBUCKS\nTotal: $5.50\nGST: $0.50",
            "currency": "AUD"
        }),
        "isBase64Encoded": False
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
