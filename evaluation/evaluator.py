import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.metrics import EvaluationMetrics

logger = logging.getLogger(__name__)


class ReceiptEvaluator:
    """Evaluates receipt parsing performance."""

    def __init__(self, predictions_file: str = None, ground_truth_file: str = None):
        self.predictions = []
        self.ground_truth = []

        if predictions_file:
            self.load_predictions(predictions_file)
        if ground_truth_file:
            self.load_ground_truth(ground_truth_file)

    def load_predictions(self, file_path: str):
        """Load predictions from file."""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.jsonl'):
                    self.predictions = [json.loads(line) for line in f]
                else:
                    self.predictions = json.load(f)
            logger.info(f"Loaded {len(self.predictions)} predictions")
        except Exception as e:
            logger.error(f"Failed to load predictions: {e}")
            raise

    def load_ground_truth(self, file_path: str):
        """Load ground truth from file."""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.jsonl'):
                    self.ground_truth = [json.loads(line) for line in f]
                else:
                    self.ground_truth = json.load(f)
            logger.info(f"Loaded {len(self.ground_truth)} ground truth samples")
        except Exception as e:
            logger.error(f"Failed to load ground truth: {e}")
            raise

    def evaluate(self) -> Dict[str, Any]:
        """Run evaluation and return results."""
        if not self.predictions or not self.ground_truth:
            raise ValueError("Both predictions and ground truth must be loaded")

        if len(self.predictions) != len(self.ground_truth):
            raise ValueError("Predictions and ground truth must have same number of samples")

        logger.info("Starting evaluation...")

        # Generate report
        report = EvaluationMetrics.generate_report(self.predictions, self.ground_truth)

        # Add additional analysis
        report.update(self._analyze_errors())
        report.update(self._calculate_confidence_intervals())

        logger.info(f"Evaluation complete. Overall score: {report['overall_score']:.3f}")

        return report

    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze common error patterns."""
        error_analysis = {
            'field_error_rates': {},
            'common_failures': []
        }

        individual_scores = EvaluationMetrics.generate_report(
            self.predictions, self.ground_truth
        )['individual_scores']

        # Calculate error rates per field
        for field in ['vendor', 'receipt_date', 'total_amount', 'gst_amount',
                     'subtotal_amount', 'items', 'currency', 'category']:
            scores = [s[field] for s in individual_scores]
            error_rate = sum(1 for s in scores if s < 0.8) / len(scores)  # < 80% accuracy
            error_analysis['field_error_rates'][field] = error_rate

        # Find common failure patterns
        failures = []
        for i, (pred, truth, scores) in enumerate(zip(
            self.predictions, self.ground_truth, individual_scores
        )):
            low_score_fields = [f for f, s in scores.items() if s < 0.5]
            if low_score_fields:
                failures.append({
                    'sample_index': i,
                    'failed_fields': low_score_fields,
                    'receipt_text': pred.get('receipt_text', '')[:100] + '...'
                })

        error_analysis['common_failures'] = failures[:10]  # Top 10 failures

        return {'error_analysis': error_analysis}

    def _calculate_confidence_intervals(self) -> Dict[str, Any]:
        """Calculate confidence intervals for scores."""
        import statistics

        report = EvaluationMetrics.generate_report(self.predictions, self.ground_truth)
        individual_scores = report['individual_scores']

        confidence_intervals = {}

        for field in ['vendor', 'receipt_date', 'total_amount', 'gst_amount',
                     'subtotal_amount', 'items', 'currency', 'category']:
            scores = [s[field] for s in individual_scores]
            if len(scores) > 1:
                mean = statistics.mean(scores)
                stdev = statistics.stdev(scores)
                # 95% confidence interval
                margin = 1.96 * stdev / (len(scores) ** 0.5)
                confidence_intervals[field] = {
                    'mean': mean,
                    'ci_lower': max(0, mean - margin),
                    'ci_upper': min(1, mean + margin)
                }

        return {'confidence_intervals': confidence_intervals}

    def save_report(self, report: Dict[str, Any], output_file: str):
        """Save evaluation report to file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            raise

    def print_summary(self, report: Dict[str, Any]):
        """Print evaluation summary."""
        print("\n" + "="*50)
        print("RECEIPT PARSING EVALUATION REPORT")
        print("="*50)

        print(f"Overall score: {report['overall_score']:.3f}")
        print(f"Total samples evaluated: {report['total_samples']}")

        print("\nField Scores:")
        for field, score in report['field_scores'].items():
            print(f"  {field:15s}: {score:.3f}")

        print("\nError Analysis (field error rates):")
        for field, rate in report['error_analysis']['field_error_rates'].items():
            print(f"  {field:15s}: {rate:.1%}")

        if report['error_analysis']['common_failures']:
            print(f"\nTop {len(report['error_analysis']['common_failures'])} Failure Cases:")
            for failure in report['error_analysis']['common_failures']:
                print(f"  Sample {failure['sample_index']}: Failed {failure['failed_fields']}")

        if report.get('confidence_intervals'):
            print("\nConfidence Intervals:")
            for field, info in report['confidence_intervals'].items():
                print(
                    f"  {field:15s}: mean={info['mean']:.3f}, "
                    f"CI95=({info['ci_lower']:.3f}, {info['ci_upper']:.3f})"
                )

        print("\n" + "="*50)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Evaluate receipt parsing performance')
    parser.add_argument('--predictions', required=True, help='Path to predictions file')
    parser.add_argument('--ground-truth', required=True, help='Path to ground truth file')
    parser.add_argument('--output', help='Path to save detailed report')

    args = parser.parse_args()

    evaluator = ReceiptEvaluator(args.predictions, args.ground_truth)
    report = evaluator.evaluate()

    evaluator.print_summary(report)

    if args.output:
        evaluator.save_report(report, args.output)
