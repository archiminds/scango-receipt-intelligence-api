"""Regression testing for receipt parsing accuracy.

RegressionRunner compares current evaluation results with a saved baseline and
flags meaningful drops. This protects parser/category changes from silently
reducing quality.
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from evaluation.evaluator import ReceiptEvaluator
from evaluation.metrics import EvaluationMetrics

logger = logging.getLogger(__name__)


class RegressionRunner:
    """Runs regression tests against synthetic data."""

    def __init__(self, test_data_path: str, results_dir: str = "evaluation/results"):
        self.test_data_path = Path(test_data_path)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)

    def run_regression_test(self, predictions: List[Dict[str, Any]],
                          test_name: str = "regression_test") -> Dict[str, Any]:
        """Run regression test and compare against baseline."""
        logger.info(f"Running regression test: {test_name}")

        # Load ground truth from the test dataset and evaluate the supplied
        # predictions against it.
        ground_truth = self._load_test_data()

        # Create evaluator
        evaluator = ReceiptEvaluator()
        evaluator.predictions = predictions
        evaluator.ground_truth = ground_truth

        # Run evaluation
        results = evaluator.evaluate()

        # Save timestamped results for history, even when no regression occurs.
        timestamp = int(time.time())
        result_file = self.results_dir / f"{test_name}_{timestamp}.json"
        evaluator.save_report(results, str(result_file))

        # Check current results against the baseline for this named test.
        regression_check = self._check_regression(results, test_name)

        return {
            'results': results,
            'regression_check': regression_check,
            'result_file': str(result_file)
        }

    def _load_test_data(self) -> List[Dict[str, Any]]:
        """Load test data from file."""
        try:
            with open(self.test_data_path, 'r') as f:
                if self.test_data_path.suffix == '.jsonl':
                    return [json.loads(line) for line in f]
                else:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load test data: {e}")
            raise

    def _check_regression(self, current_results: Dict[str, Any],
                         test_name: str) -> Dict[str, Any]:
        """Check for performance regressions against baseline."""
        baseline_file = self.results_dir / f"{test_name}_baseline.json"

        if not baseline_file.exists():
            logger.info("No baseline found, creating new baseline")
            self._save_baseline(current_results, baseline_file)
            return {
                'has_regression': False,
                'message': 'New baseline created',
                'changes': {}
            }

        # Load baseline
        try:
            with open(baseline_file, 'r') as f:
                baseline = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load baseline: {e}")
            return {
                'has_regression': False,
                'message': f'Failed to load baseline: {e}',
                'changes': {}
            }

        # Compare scores with a fixed tolerance. A 5% drop is treated as
        # meaningful enough to investigate.
        changes = {}
        has_regression = False
        regression_threshold = 0.05  # 5% drop

        current_overall = current_results['overall_score']
        baseline_overall = baseline['overall_score']

        if current_overall < baseline_overall - regression_threshold:
            has_regression = True
            changes['overall_score'] = {
                'baseline': baseline_overall,
                'current': current_overall,
                'change': current_overall - baseline_overall
            }

        # Check individual fields
        for field in current_results['field_scores']:
            current_score = current_results['field_scores'][field]
            baseline_score = baseline['field_scores'].get(field, 0)

            if current_score < baseline_score - regression_threshold:
                has_regression = True
                changes[field] = {
                    'baseline': baseline_score,
                    'current': current_score,
                    'change': current_score - baseline_score
                }

        if has_regression:
            message = f"Regression detected! Overall score dropped by {baseline_overall - current_overall:.3f}"
        else:
            message = "No regression detected"

        return {
            'has_regression': has_regression,
            'message': message,
            'changes': changes
        }

    def _save_baseline(self, results: Dict[str, Any], baseline_file: Path):
        """Save current results as baseline."""
        try:
            with open(baseline_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Baseline saved to {baseline_file}")
        except Exception as e:
            logger.error(f"Failed to save baseline: {e}")

    def update_baseline(self, test_name: str):
        """Update baseline with latest results."""
        baseline_file = self.results_dir / f"{test_name}_baseline.json"
        latest_result_file = self._find_latest_result(test_name)

        if latest_result_file:
            try:
                with open(latest_result_file, 'r') as f:
                    results = json.load(f)
                self._save_baseline(results, baseline_file)
                logger.info(f"Baseline updated for {test_name}")
            except Exception as e:
                logger.error(f"Failed to update baseline: {e}")
        else:
            logger.error(f"No result files found for {test_name}")

    def _find_latest_result(self, test_name: str) -> Optional[Path]:
        """Find the latest result file for a test."""
        result_files = list(self.results_dir.glob(f"{test_name}_*.json"))
        if not result_files:
            return None

        # Filter out baseline files and sort by timestamp in filename
        timestamp_files = []
        for f in result_files:
            parts = f.stem.split('_')
            if len(parts) >= 2 and parts[-1].isdigit():
                timestamp_files.append(f)

        if not timestamp_files:
            return None

        timestamp_files.sort(key=lambda x: int(x.stem.split('_')[-1]), reverse=True)
        return timestamp_files[0]

    def run_batch_tests(self, prediction_batches: List[List[Dict[str, Any]]],
                       test_names: List[str]) -> List[Dict[str, Any]]:
        """Run multiple regression tests in batch."""
        results = []

        for predictions, test_name in zip(prediction_batches, test_names):
            try:
                result = self.run_regression_test(predictions, test_name)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to run test {test_name}: {e}")
                results.append({
                    'test_name': test_name,
                    'error': str(e)
                })

        return results

    def generate_regression_report(self, test_results: List[Dict[str, Any]],
                                 output_file: str):
        """Generate comprehensive regression report."""
        report = {
            'timestamp': int(time.time()),
            'summary': {
                'total_tests': len(test_results),
                'passed_tests': sum(1 for r in test_results if not r.get('regression_check', {}).get('has_regression', False)),
                'failed_tests': sum(1 for r in test_results if r.get('regression_check', {}).get('has_regression', False)),
                'error_tests': sum(1 for r in test_results if 'error' in r)
            },
            'test_results': test_results
        }

        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Regression report saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save regression report: {e}")

        return report


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run regression tests for receipt parsing')
    parser.add_argument('--test-data', required=True, help='Path to test data file')
    parser.add_argument('--predictions', required=True, help='Path to predictions file')
    parser.add_argument('--test-name', default='regression_test', help='Name of the test')
    parser.add_argument('--results-dir', default='evaluation/results', help='Results directory')
    parser.add_argument('--update-baseline', action='store_true', help='Update baseline with current results')

    args = parser.parse_args()

    runner = RegressionRunner(args.test_data, args.results_dir)

    # Load predictions
    with open(args.predictions, 'r') as f:
        if args.predictions.endswith('.jsonl'):
            predictions = [json.loads(line) for line in f]
        else:
            predictions = json.load(f)

    if args.update_baseline:
        runner.update_baseline(args.test_name)
        print(f"Baseline updated for {args.test_name}")
    else:
        result = runner.run_regression_test(predictions, args.test_name)
        print(f"Test completed. Results saved to: {result['result_file']}")
        print(f"Regression check: {result['regression_check']['message']}")
