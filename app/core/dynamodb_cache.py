import boto3
import json
import logging
import time
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, BotoCoreError
from app.models.schemas import CacheEntry

logger = logging.getLogger(__name__)


class DynamoDBCacheError(Exception):
    """Custom exception for DynamoDB cache errors."""
    pass


class DynamoDBCacheClient:
    """DynamoDB client for receipt caching with TTL support."""

    def __init__(self, table_name: str, region: str = 'us-east-1',
                 dynamodb_client: Optional[Any] = None):
        """
        Initialize DynamoDB cache client.

        Args:
            table_name: DynamoDB table name
            region: AWS region
            dynamodb_client: Optional injected boto3 client for testing
        """
        self.table_name = table_name
        self.region = region
        self.dynamodb = dynamodb_client or boto3.client('dynamodb', region_name=region)
        logger.info(f"Initialized DynamoDB cache client for table {table_name} in region {region}")

    def get_cached_result(self, request_hash: str) -> Optional[CacheEntry]:
        """
        Retrieve cached result from DynamoDB.

        Args:
            hash_key: SHA-256 hash of the receipt text

        Returns:
            CacheEntry if found and not expired, None otherwise

        Raises:
            DynamoDBCacheError: If retrieval fails due to client errors
        """
        try:
            logger.debug(f"Checking cache for request_hash: {request_hash}")

            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={
                    'request_hash': {'S': request_hash}
                }
            )

            if 'Item' in response:
                item = response['Item']
                # Check if TTL has expired
                ttl = int(item.get('ttl', {}).get('N', 0))
                current_time = int(time.time())

                if current_time < ttl:
                    logger.debug(f"Cache hit for request_hash: {request_hash}")
                    # Deserialize the cached response
                    response_data = json.loads(item['response']['S'])
                    # Convert back to ReceiptParseResponse
                    from app.models.schemas import ReceiptParseResponse
                    cached_response = ReceiptParseResponse(**response_data)
                    return CacheEntry(
                        request_hash=request_hash,
                        receipt_text=item['receipt_text']['S'],
                        response=response_data,
                        ttl=ttl
                    )
                else:
                    logger.debug(f"Cache expired for request_hash: {request_hash}, deleting")
                    self._delete_expired_item(request_hash)

            logger.debug(f"Cache miss for request_hash: {request_hash}")
            return None

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"DynamoDB get error [{error_code}]: {e}")
            raise DynamoDBCacheError(f"DynamoDB get error: {e}") from e
        except BotoCoreError as e:
            logger.error(f"DynamoDB client error: {e}")
            raise DynamoDBCacheError(f"DynamoDB client error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize cached response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in cache retrieval: {e}", exc_info=True)
            raise DynamoDBCacheError(f"Unexpected error in cache retrieval: {e}") from e

    def save_to_cache(self, cache_entry: CacheEntry) -> bool:
        """
        Save result to DynamoDB cache with TTL.

        Args:
            cache_entry: Cache entry to save

        Returns:
            True if saved successfully, False otherwise

        Raises:
            DynamoDBCacheError: If save fails due to client errors
        """
        try:
            logger.debug(f"Saving cache entry for request_hash: {cache_entry.request_hash}")

            # Serialize the response
            response_json = json.dumps(cache_entry.response, default=str)

            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    'request_hash': {'S': cache_entry.request_hash},
                    'receipt_text': {'S': cache_entry.receipt_text},
                    'response': {'S': response_json},
                    'ttl': {'N': str(cache_entry.ttl)}
                }
            )

            logger.debug(f"Successfully cached result for request_hash: {cache_entry.request_hash}")
            return True

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"DynamoDB put error [{error_code}]: {e}")
            raise DynamoDBCacheError(f"DynamoDB put error: {e}") from e
        except BotoCoreError as e:
            logger.error(f"DynamoDB client error: {e}")
            raise DynamoDBCacheError(f"DynamoDB client error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error in cache save: {e}", exc_info=True)
            raise DynamoDBCacheError(f"Unexpected error in cache save: {e}") from e

    def _delete_expired_item(self, request_hash: str):
        """
        Delete expired cache item.

        Args:
            hash_key: Hash key of the expired item
        """
        try:
            self.dynamodb.delete_item(
                TableName=self.table_name,
                Key={
                    'request_hash': {'S': request_hash}
                }
            )
            logger.debug(f"Deleted expired cache item: {request_hash}")
        except Exception as e:
            logger.warning(f"Failed to delete expired cache item {request_hash}: {e}")
