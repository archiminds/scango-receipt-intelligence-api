"""Receipt expense categorization.

The categorizer uses deterministic keyword rules first and only falls back to
AI for ambiguous cases. This keeps common categories cheap, explainable, and
stable for regression tests.
"""

import re
import logging
from typing import List, Optional, Dict, Any
from app.models.schemas import CategorizationResult
from app.core.bedrock_client import BedrockClient
from app.core.normalizer import Normalizer

logger = logging.getLogger(__name__)


class Categorizer:
    """Handles hybrid categorization using rules first, then AI for ambiguous cases."""

    # Categorization rules based on keywords
    RULES = {
        'Car': [
            'bp', 'ampol', 'caltex', 'shell', 'car park', 'point parking',
            'motorserve', 'nrma', 'linkt', 'car rental', 'fuel', 'petrol'
        ],
        'Travel': [
            'uber', 'taxi', 'airlines', 'philippines airlines', 'singapore airlines',
            'transport', '7-eleven', 'linkt', 'parking', 'flight', 'airfare'
        ],
        'Utilities': [
            'agl', 'amaysim', 'optus', 'telstra', 'water', 'internet service', 'mobile plan'
        ],
        'Equipment': [
            'safe', 'speaker', 'keyboard', 'monitor', 'storage', 'checkers', 'laptop', 'printer'
        ],
        'Food': [
            'nandos', 'absolute thai', 'chef noodles', 'espresso', 'dominos',
            'dosa hut', 'arjun indian', 'betty burger', 'restaurant', 'bakery',
            'flat white', 'banana bread', 'coffee'
        ],
        'Staff Amenities': [
            'aldi', 'coles', 'woolworths', 'amazon', 'milk', 'bread', 'eggs', 'snacks',
            'reusable bag'
        ],
        'Office Supplies': [
            'hp instant ink', 'stationery', 'amazon', 'jb hi-fi', 'ink', 'paper',
            'notebook', 'pen', 'printer paper'
        ],
        'Accounting Fee': [
            'accountant fee', 'sjb', 'xero', 'myob'
        ],
        'Operational Cost': [
            'gsuite', 'google', 'apple subscriptions', 'chatgpt', 'asic',
            'flick', 'ableton', 'software', 'subscription', 'gopro', 'aws', 'azure'
        ]
    }

    def __init__(self, bedrock_client: Optional[BedrockClient] = None):
        self.bedrock_client = bedrock_client

    def categorize(self, vendor: Optional[str], items: List[Any],
                  receipt_text: str) -> CategorizationResult:
        """Main categorization method using hybrid approach."""
        # Receipt items may arrive as Pydantic ParsedItem objects from the main
        # service or as dictionaries in tests/synthetic data.
        item_names = []
        for item in items:
            if hasattr(item, 'name'):
                item_names.append(item.name)
            elif isinstance(item, dict):
                item_names.append(item.get('name', ''))
            else:
                item_names.append(str(item))

        text_to_analyze = f"{vendor or ''} {' '.join(item_names)} {receipt_text}".lower()

        # Try rule-based categorization first. A high-confidence rules result is
        # returned immediately because it is auditable and avoids another model
        # call.
        rule_result = self._categorize_by_rules(text_to_analyze)
        fallback_rule_result = None
        if rule_result:
            fallback_rule_result = rule_result
            if rule_result.confidence >= 0.8:
                return rule_result

        # If rules are ambiguous, use AI. The current implementation returns an
        # unclassified placeholder, so the fallback rule result below remains
        # important.
        if self.bedrock_client:
            ai_result = self._categorize_by_ai(vendor, items, receipt_text)
            if ai_result and ai_result.category.lower() != 'unclassified':
                return ai_result

        if fallback_rule_result:
            return fallback_rule_result

        # Fallback to Unclassified when neither rules nor AI produce a useful
        # category. This avoids fabricating a confident business category.
        return CategorizationResult(
            category='Unclassified',
            source='fallback',
            reason='No clear categorization found',
            confidence=0.0
        )

    def _categorize_by_rules(self, text: str) -> Optional[CategorizationResult]:
        """Rule-based categorization."""
        matches = {}

        for category, keywords in self.RULES.items():
            category_matches = []
            for keyword in keywords:
                if keyword.lower() in text:
                    category_matches.append(keyword)

            if category_matches:
                matches[category] = category_matches

        if not matches:
            return None

        # Find category with the most keyword evidence. Ties use dict order,
        # which is stable in modern Python but should not be treated as a
        # business rule.
        best_category = max(matches.keys(), key=lambda c: len(matches[c]))
        matched_keywords = matches[best_category]

        # Confidence is intentionally simple: more independent keyword matches
        # increase confidence up to 1.0.
        confidence = min(len(matched_keywords) * 0.3, 1.0)

        return CategorizationResult(
            category=best_category,
            source='rules',
            reason=f"Matched keywords: {', '.join(matched_keywords)}",
            matched_keywords=matched_keywords,
            confidence=confidence
        )

    def _categorize_by_ai(self, vendor: Optional[str], items: List[Dict[str, Any]],
                         receipt_text: str) -> Optional[CategorizationResult]:
        """AI-based categorization for ambiguous cases."""
        if not self.bedrock_client:
            return None

        try:
            prompt = self._build_categorization_prompt(vendor, items, receipt_text)

            # For now, return a placeholder - TODO: Implement actual Bedrock categorization
            # This would use the same invoke_model pattern as parse_receipt
            return CategorizationResult(
                category='Unclassified',  # TODO: Replace with actual AI categorization
                source='ai',
                reason='AI categorization not yet fully implemented - using fallback',
                confidence=0.5
            )
        except Exception as e:
            logger.warning(f"AI categorization failed: {e}")
            return None

    def _build_categorization_prompt(self, vendor: Optional[str],
                                   items: List[Dict[str, Any]], receipt_text: str) -> str:
        """Build prompt for AI categorization."""
        categories = list(self.RULES.keys()) + ['Unclassified']

        items_text = '\n'.join([f"- {item.get('name', '')}" for item in items])

        return f"""
Categorize this receipt into one of the following categories:
{', '.join(categories)}

Vendor: {vendor or 'Unknown'}
Items:
{items_text}

Receipt text:
{receipt_text}

Return only the category name and a brief reason.
"""
