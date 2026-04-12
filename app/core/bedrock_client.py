import boto3
import json
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError
from app.models.schemas import BedrockParseRequest, BedrockParseResponse

logger = logging.getLogger(__name__)


class BedrockClientError(Exception):
    """Custom exception for Bedrock client errors."""
    pass


class BedrockClient:
    """Client for interacting with Amazon Bedrock Nova."""

    def __init__(self, model_id: str, region: str = 'us-east-1',
                 bedrock_client: Optional[Any] = None):
        """
        Initialize Bedrock client.

        Args:
            model_id: Bedrock model identifier
            region: AWS region
            bedrock_client: Optional injected boto3 client for testing
        """
        self.model_id = model_id
        self.region = region
        self.client = bedrock_client or boto3.client('bedrock-runtime', region_name=region)
        logger.info(f"Initialized Bedrock client for model {model_id} in region {region}")

    def parse_receipt(self, request: BedrockParseRequest) -> Optional[BedrockParseResponse]:
        """
        Parse receipt text using Bedrock Nova.

        Args:
            request: Bedrock parse request

        Returns:
            Parsed receipt data or None if parsing failed

        Raises:
            BedrockClientError: If parsing fails due to client errors
        """
        try:
            logger.debug(f"Parsing receipt with Bedrock model {self.model_id}")

            prompt = self._build_parse_prompt(request.receipt_text, request.currency)

            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 1000,
                    "temperature": 0.1
                }
            }

            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType='application/json',
                accept='application/json'
            )

            response_body = json.loads(response['body'].read())
            parsed_data = self._extract_structured_data(response_body)

            if parsed_data:
                logger.debug("Successfully parsed receipt with Bedrock")
                return BedrockParseResponse(**parsed_data)
            else:
                logger.warning("Bedrock returned empty or invalid response")
                return None

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Bedrock API error [{error_code}]: {error_message}")
            raise BedrockClientError(f"Bedrock API error: {error_message}") from e
        except BotoCoreError as e:
            logger.error(f"Bedrock client error: {e}")
            raise BedrockClientError(f"Bedrock client error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bedrock response JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Bedrock parsing: {e}", exc_info=True)
            raise BedrockClientError(f"Unexpected error in Bedrock parsing: {e}") from e

    def _build_parse_prompt(self, receipt_text: str, currency: str) -> str:
        """Build the prompt for receipt parsing."""
        return f"""
Parse the following receipt text and extract structured information.
Return ONLY a valid JSON object with the following structure:
{{
    "vendor": "store name or null",
    "receipt_date": "YYYY-MM-DD or null",
    "items": [
        {{
            "name": "item name",
            "quantity": 1,
            "unit_price": 10.50,
            "total_price": 10.50
        }}
    ],
    "subtotal_amount": 10.50,
    "total_amount": 11.55,
    "gst_amount": 1.05,
    "currency": "{currency}"
}}

Rules:
- Extract vendor name from the receipt
- Parse date in YYYY-MM-DD format
- Extract all items with their prices
- Calculate amounts as decimal numbers
- If GST is not explicitly mentioned, leave gst_amount as null
- Be precise with numbers and dates

Receipt text:
{receipt_text}
"""

    def _extract_structured_data(self, response_body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract structured data from Bedrock response."""
        try:
            content = response_body.get('content', [{}])[0].get('text', '')
            if not content:
                return None

            # Try to parse JSON from the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                return None

            json_str = content[start_idx:end_idx]
            return json.loads(json_str)

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse Bedrock response: {e}")
            return None