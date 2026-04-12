import re
from typing import Dict, List, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
from difflib import SequenceMatcher


class EvaluationMetrics:
    """Metrics for evaluating receipt parsing performance."""

    @staticmethod
    def calculate_accuracy(predicted: Any, expected: Any, field: str) -> float:
        """Calculate accuracy for a specific field."""
        if field in ['vendor', 'category']:
            return EvaluationMetrics._text_similarity(predicted or '', expected or '')

        elif field in ['total_amount', 'subtotal_amount', 'gst_amount']:
            return EvaluationMetrics._amount_accuracy(predicted, expected)

        elif field == 'receipt_date':
            return EvaluationMetrics._date_accuracy(predicted, expected)

        elif field == 'items':
            return EvaluationMetrics._items_accuracy(predicted or [], expected or [])

        elif field == 'currency':
            return 1.0 if (predicted or '').upper() == (expected or '').upper() else 0.0

        return 0.0

    @staticmethod
    def _text_similarity(text1: str, text2: str) -> float:
        """Calculate text similarity using sequence matcher."""
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0

        # Normalize text
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()

        return SequenceMatcher(None, text1, text2).ratio()

    @staticmethod
    def _amount_accuracy(predicted: Optional[Decimal], expected: Optional[Decimal]) -> float:
        """Calculate accuracy for monetary amounts."""
        if predicted is None and expected is None:
            return 1.0
        if predicted is None or expected is None:
            return 0.0

        # Convert to Decimal if needed
        if not isinstance(predicted, Decimal):
            try:
                predicted = Decimal(str(predicted))
            except:
                return 0.0
        if not isinstance(expected, Decimal):
            try:
                expected = Decimal(str(expected))
            except:
                return 0.0

        # Exact match
        if predicted == expected:
            return 1.0

        # Within 1 cent
        diff = abs(predicted - expected)
        if diff <= Decimal('0.01'):
            return 0.9

        # Within 10 cents
        if diff <= Decimal('0.10'):
            return 0.5

        # Within $1
        if diff <= Decimal('1.00'):
            return 0.1

        return 0.0

    @staticmethod
    def _date_accuracy(predicted: Optional[str], expected: Optional[str]) -> float:
        """Calculate accuracy for dates."""
        if not predicted and not expected:
            return 1.0
        if not predicted or not expected:
            return 0.0

        # Try to parse dates
        try:
            from datetime import datetime
            pred_date = datetime.fromisoformat(predicted)
            exp_date = datetime.fromisoformat(expected)

            if pred_date == exp_date:
                return 1.0

            # Same day
            if pred_date.date() == exp_date.date():
                return 0.8

            # Same month
            if pred_date.month == exp_date.month and pred_date.year == exp_date.year:
                return 0.5

        except:
            pass

        return 0.0

    @staticmethod
    def _items_accuracy(predicted_items: List[Dict[str, Any]],
                       expected_items: List[Dict[str, Any]]) -> float:
        """Calculate accuracy for items list."""
        if not predicted_items and not expected_items:
            return 1.0
        if not predicted_items or not expected_items:
            return 0.0

        total_score = 0.0
        max_items = max(len(predicted_items), len(expected_items))

        # Simple matching based on name similarity
        for pred_item in predicted_items:
            best_match = 0.0
            for exp_item in expected_items:
                name_sim = EvaluationMetrics._text_similarity(
                    pred_item.get('name', ''),
                    exp_item.get('name', '')
                )
                price_sim = EvaluationMetrics._amount_accuracy(
                    pred_item.get('total_price'),
                    exp_item.get('total_price')
                )
                match_score = (name_sim + price_sim) / 2
                best_match = max(best_match, match_score)

            total_score += best_match

        return total_score / max_items if max_items > 0 else 0.0

    @staticmethod
    def calculate_overall_score(results: Dict[str, float],
                               weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate weighted overall score."""
        if not weights:
            weights = {
                'vendor': 0.1,
                'receipt_date': 0.1,
                'total_amount': 0.25,
                'gst_amount': 0.15,
                'subtotal_amount': 0.1,
                'items': 0.15,
                'currency': 0.05,
                'category': 0.1
            }

        total_weight = 0.0
        weighted_score = 0.0

        for field, score in results.items():
            if field in weights:
                weight = weights[field]
                weighted_score += score * weight
                total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    @staticmethod
    def generate_report(predictions: List[Dict[str, Any]],
                       ground_truth: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive evaluation report."""
        if len(predictions) != len(ground_truth):
            raise ValueError("Predictions and ground truth must have same length")

        field_scores = {}
        individual_scores = []

        for pred, truth in zip(predictions, ground_truth):
            pred_output = pred.get('expected_output', pred)
            truth_output = truth.get('expected_output', truth)

            scores = {}
            for field in ['vendor', 'receipt_date', 'total_amount', 'gst_amount',
                         'subtotal_amount', 'items', 'currency', 'category']:
                pred_val = pred_output.get(field)
                truth_val = truth_output.get(field)
                scores[field] = EvaluationMetrics.calculate_accuracy(pred_val, truth_val, field)

            individual_scores.append(scores)

            # Accumulate field scores
            for field, score in scores.items():
                if field not in field_scores:
                    field_scores[field] = []
                field_scores[field].append(score)

        # Calculate averages
        avg_scores = {}
        for field, scores in field_scores.items():
            avg_scores[field] = sum(scores) / len(scores)

        overall_score = EvaluationMetrics.calculate_overall_score(avg_scores)

        return {
            'overall_score': overall_score,
            'field_scores': avg_scores,
            'individual_scores': individual_scores,
            'total_samples': len(predictions)
        }