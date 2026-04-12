from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid


class ReceiptParseRequest(BaseModel):
    """Request model for receipt parsing API."""
    receipt_text: str = Field(..., description="OCR-extracted receipt text to parse")
    source: Optional[str] = Field(None, description="Source system identifier (e.g., 'mobile_app', 'web')")
    currency: Optional[str] = Field("AUD", description="ISO currency code, defaults to AUD")
    user_id: Optional[str] = Field(None, description="Unique user identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional request metadata")

    @validator('receipt_text')
    def validate_receipt_text(cls, v):
        if not v or not v.strip():
            raise ValueError("receipt_text cannot be empty")
        return v.strip()

    @validator('currency')
    def validate_currency(cls, v):
        if v and len(v) != 3:
            raise ValueError("currency must be a 3-letter ISO code")
        return v.upper() if v else v


class ParsedItem(BaseModel):
    """Model for individual receipt items."""
    name: str = Field(..., description="Item name or description")
    quantity: Optional[int] = Field(1, description="Item quantity", ge=1)
    unit_price: Optional[Decimal] = Field(None, description="Price per unit", ge=0)
    total_price: Optional[Decimal] = Field(None, description="Total price for this item", ge=0)

    @validator('total_price', 'unit_price')
    def validate_prices(cls, v):
        return round(v, 2) if v is not None else v


class ReceiptParseResponse(BaseModel):
    """Response model for receipt parsing API."""
    vendor: Optional[str] = Field(None, description="Extracted vendor/store name")
    receipt_date: Optional[str] = Field(None, description="Receipt date in YYYY-MM-DD format")
    items: List[ParsedItem] = Field(default_factory=list, description="List of parsed items")
    subtotal_amount: Optional[Decimal] = Field(None, description="Subtotal before GST", ge=0)
    total_amount: Optional[Decimal] = Field(None, description="Total amount including GST", ge=0)
    gst_amount: Optional[Decimal] = Field(None, description="GST amount", ge=0)
    currency: str = Field("AUD", description="ISO currency code")
    category: str = Field(..., description="Business expense category")
    categorization_source: str = Field(..., description="Categorization method: 'rules' or 'ai'")
    categorization_reason: str = Field(..., description="Explanation of categorization decision")
    matched_keywords: List[str] = Field(default_factory=list, description="Keywords that matched categorization rules")
    confidence_score: float = Field(..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    cache_status: str = Field(..., description="Cache status: 'hit' or 'miss'")
    request_id: str = Field(..., description="Unique request identifier")
    warnings: List[str] = Field(default_factory=list, description="Non-critical warnings")

    @validator('request_id')
    def validate_request_id(cls, v):
        if not v:
            return str(uuid.uuid4())
        return v

    @validator('total_amount', 'subtotal_amount', 'gst_amount')
    def validate_amounts(cls, v):
        return round(v, 2) if v is not None else v


class CacheEntry(BaseModel):
    """Model for DynamoDB cache entries."""
    hash_key: str = Field(..., description="SHA-256 hash of normalized receipt text")
    receipt_text: str = Field(..., description="Original receipt text")
    response: Dict[str, Any] = Field(..., description="Cached response data")
    ttl: int = Field(..., description="TTL timestamp for DynamoDB expiration", gt=0)


class BedrockParseRequest(BaseModel):
    """Request model for Bedrock parsing."""
    receipt_text: str = Field(..., description="Receipt text to send to Bedrock")
    currency: str = Field("AUD", description="Currency context for parsing")


class BedrockParseResponse(BaseModel):
    """Response model from Bedrock parsing."""
    vendor: Optional[str] = None
    receipt_date: Optional[str] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)
    subtotal_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    gst_amount: Optional[Decimal] = None
    currency: str = "AUD"


class CategorizationResult(BaseModel):
    """Result model for receipt categorization."""
    category: str = Field(..., description="Assigned category")
    source: str = Field(..., description="Categorization source: 'rules' or 'ai'")
    reason: str = Field(..., description="Reason for categorization")
    matched_keywords: List[str] = Field(default_factory=list, description="Matched keywords")
    confidence: float = Field(..., description="Confidence score", ge=0.0, le=1.0)