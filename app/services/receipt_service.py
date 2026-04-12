import logging
import os
import time
from typing import Optional
from app.models.schemas import (
    ReceiptParseRequest, ReceiptParseResponse, CacheEntry,
    BedrockParseRequest, CategorizationResult
)
from app.core.preprocessor import Preprocessor
from app.core.bedrock_client import BedrockClient, BedrockClientError
from app.core.normalizer import Normalizer
from app.core.categorizer import Categorizer
from app.core.validator import Validator
from app.core.postprocessor import Postprocessor
from app.core.dynamodb_cache import DynamoDBCacheClient, DynamoDBCacheError
from app.core.parser import Parser

logger = logging.getLogger(__name__)


class ReceiptServiceError(Exception):
    """Custom exception for receipt service errors."""
    pass


class ReceiptService:
    """Central service for receipt parsing orchestration."""

    def __init__(self, bedrock_client: Optional[BedrockClient] = None,
                 cache_client: Optional[DynamoDBCacheClient] = None):
        """
        Initialize service with injectable clients for testability.

        Args:
            bedrock_client: Optional injected Bedrock client
            cache_client: Optional injected DynamoDB cache client
        """
        self.bedrock_client = bedrock_client or BedrockClient(
            model_id=os.getenv('BEDROCK_MODEL_ID', 'amazon.nova-pro-v1:0'),
            region=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.categorizer = Categorizer(self.bedrock_client)
        self.cache_client = cache_client or DynamoDBCacheClient(
            table_name=os.getenv('DYNAMODB_TABLE_NAME', 'scango-receipt-cache'),
            region=os.getenv('AWS_REGION', 'us-east-1')
        )
        logger.info("Initialized ReceiptService")

    def parse_receipt(self, request: ReceiptParseRequest) -> ReceiptParseResponse:
        """
        Main method to parse a receipt with comprehensive error handling.

        Args:
            request: Receipt parse request

        Returns:
            Parsed receipt response

        Raises:
            ReceiptServiceError: If parsing fails critically
        """
        request_id = Postprocessor.generate_request_id()
        logger.info(f"Processing receipt parse request: {request_id}")

        try:
            # Step 1: Validate request
            self._validate_request(request)

            # Step 2: Clean and normalize OCR text
            cleaned_text = Preprocessor.clean_text(request.receipt_text)
            normalized_text = Preprocessor.normalize_text(cleaned_text)
            logger.debug(f"Preprocessed text for request {request_id}")

            # Step 3: Generate hash for caching
            text_hash = Postprocessor.hash_text(normalized_text)

            # Step 4: Check cache
            cached_response = self._check_cache(text_hash)
            if cached_response:
                logger.info(f"Cache hit for request: {request_id}")
                cached_response.cache_status = 'hit'
                cached_response.request_id = request_id
                return cached_response

            # Step 5: Parse with Bedrock
            logger.info(f"Cache miss, parsing with AI for request: {request_id}")
            bedrock_request = BedrockParseRequest(
                receipt_text=cleaned_text,
                currency=request.currency or 'AUD'
            )
            
            try:
                bedrock_response = self.bedrock_client.parse_receipt(bedrock_request)
                if bedrock_response:
                    parsed_data = Parser.parse_bedrock_response(bedrock_response)
                else:
                    logger.warning(f"Bedrock parsing returned None for request {request_id}, using fallback")
                    parsed_data = Parser.extract_key_fields(cleaned_text)
            except BedrockClientError as e:
                logger.warning(f"Bedrock parsing failed for request {request_id}: {e}, using fallback")
                parsed_data = Parser.extract_key_fields(cleaned_text)

            # Step 6: Normalize extracted values
            normalized_data = self._normalize_parsed_data(parsed_data, request.currency)
            logger.debug(f"Normalized data for request {request_id}")

            # Step 7: Compute GST if missing
            normalized_data['gst_amount'] = Normalizer.compute_gst(
                normalized_data.get('total_amount'),
                normalized_data.get('gst_amount')
            )

            # Step 8: Categorize
            categorization = self.categorizer.categorize(
                normalized_data.get('vendor'),
                normalized_data.get('items', []),
                cleaned_text
            )
            logger.debug(f"Categorized receipt for request {request_id}: {categorization.category}")

            # Step 9: Build response
            response = ReceiptParseResponse(
                vendor=normalized_data.get('vendor'),
                receipt_date=normalized_data.get('receipt_date'),
                items=normalized_data.get('items', []),
                subtotal_amount=normalized_data.get('subtotal_amount'),
                total_amount=normalized_data.get('total_amount'),
                gst_amount=normalized_data['gst_amount'],
                currency=normalized_data.get('currency', request.currency or 'AUD'),
                category=categorization.category,
                categorization_source=categorization.source,
                categorization_reason=categorization.reason,
                matched_keywords=categorization.matched_keywords,
                confidence_score=categorization.confidence,
                cache_status='miss',
                request_id=request_id,
                warnings=[]
            )

            # Step 10: Validate
            warnings = Validator.validate_response(response)
            response.warnings = warnings
            if warnings:
                logger.warning(f"Validation warnings for request {request_id}: {warnings}")

            # Step 11: Finalize response
            final_response = Postprocessor.finalize_response(
                response, request_id, 'miss', warnings
            )

            # Step 12: Cache result
            self._save_to_cache(text_hash, normalized_text, final_response)

            logger.info(f"Successfully processed request: {request_id}")
            return final_response

        except DynamoDBCacheError as e:
            logger.error(f"Cache error for request {request_id}: {e}")
            # Continue without caching, but don't fail the request
            logger.warning(f"Continuing without caching due to cache error: {e}")
            return self._create_error_response(request_id, f"Cache error: {e}")
        except ValueError as e:
            logger.error(f"Validation error for request {request_id}: {e}")
            raise ReceiptServiceError(f"Invalid request data: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error processing request {request_id}: {e}", exc_info=True)
            raise ReceiptServiceError(f"Unexpected error: {e}") from e

    def _validate_request(self, request: ReceiptParseRequest):
        """
        Validate incoming request.

        Args:
            request: Receipt parse request

        Raises:
            ValueError: If request validation fails
        """
        if not request.receipt_text or not request.receipt_text.strip():
            raise ValueError("Receipt text is required and cannot be empty")

    def _check_cache(self, text_hash: str) -> Optional[ReceiptParseResponse]:
        """
        Check DynamoDB cache for existing result.

        Args:
            text_hash: SHA-256 hash of normalized receipt text

        Returns:
            Cached response if found, None otherwise
        """
        try:
            cached_entry = self.cache_client.get_cached_result(text_hash)
            if cached_entry:
                # Convert the cached response back to ReceiptParseResponse
                from app.models.schemas import ReceiptParseResponse
                return ReceiptParseResponse(**cached_entry.response)
            return None
        except DynamoDBCacheError as e:
            logger.warning(f"Cache check failed: {e}")
            return None

    def _save_to_cache(self, text_hash: str, normalized_text: str,
                      response: ReceiptParseResponse):
        """
        Save result to DynamoDB cache with TTL.

        Args:
            text_hash: SHA-256 hash of the receipt text
            normalized_text: Normalized receipt text
            response: Response to cache
        """
        try:
            ttl_days = int(os.getenv('CACHE_TTL_DAYS', '30'))
            ttl_seconds = ttl_days * 24 * 60 * 60
            ttl_timestamp = int(time.time()) + ttl_seconds

            cache_entry = CacheEntry(
                hash_key=text_hash,
                receipt_text=normalized_text,
                response={
                    'vendor': response.vendor,
                    'receipt_date': response.receipt_date,
                    'items': [item.model_dump() if hasattr(item, 'model_dump') else item.__dict__ for item in response.items],
                    'subtotal_amount': str(response.subtotal_amount) if response.subtotal_amount else None,
                    'total_amount': str(response.total_amount) if response.total_amount else None,
                    'gst_amount': str(response.gst_amount) if response.gst_amount else None,
                    'currency': response.currency,
                    'category': response.category,
                    'categorization_source': response.categorization_source,
                    'categorization_reason': response.categorization_reason,
                    'matched_keywords': response.matched_keywords,
                    'confidence_score': response.confidence_score,
                    'cache_status': response.cache_status,
                    'request_id': response.request_id,
                    'warnings': response.warnings
                },
                ttl=ttl_timestamp
            )
            self.cache_client.save_to_cache(cache_entry)
            logger.debug(f"Cached result for hash: {text_hash}")
        except DynamoDBCacheError as e:
            logger.warning(f"Cache save failed: {e}")

    def _normalize_parsed_data(self, parsed_data: dict, currency: Optional[str]) -> dict:
        """
        Normalize parsed data from Bedrock or fallback parser.

        Args:
            parsed_data: Raw parsed data
            currency: Request currency

        Returns:
            Normalized data dictionary
        """
        return {
            'vendor': parsed_data.get('vendor'),
            'receipt_date': parsed_data.get('receipt_date'),
            'items': parsed_data.get('items', []),
            'subtotal_amount': Normalizer.normalize_amount(parsed_data.get('subtotal_amount')),
            'total_amount': Normalizer.normalize_amount(parsed_data.get('total_amount')),
            'gst_amount': Normalizer.normalize_amount(parsed_data.get('gst_amount')),
            'currency': parsed_data.get('currency', currency or 'AUD')
        }

    def _create_error_response(self, request_id: str, error_message: str) -> ReceiptParseResponse:
        """
        Create an error response when parsing fails but we want to return something.

        Args:
            request_id: Request identifier
            error_message: Error message

        Returns:
            Error response
        """
        return ReceiptParseResponse(
            vendor=None,
            receipt_date=None,
            items=[],
            subtotal_amount=None,
            total_amount=None,
            gst_amount=None,
            currency='AUD',
            category='Unclassified',
            categorization_source='error',
            categorization_reason='Parsing failed',
            matched_keywords=[],
            confidence_score=0.0,
            cache_status='error',
            request_id=request_id,
            warnings=[error_message]
        )