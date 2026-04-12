#!/usr/bin/env python3
"""
Simple regression test flow for receipt parsing API.
This script generates synthetic data, runs evaluation, and checks for regressions.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from synthetic.generator import SyntheticDataGenerator
from evaluation.evaluator import ReceiptEvaluator
from evaluation.regression_runner import RegressionRunner


def main():
    """Run the regression test flow."""
    print("Starting regression test flow...")

    # Create directories
    synthetic_dir = project_root / "synthetic"
    evaluation_dir = project_root / "evaluation"
    results_dir = evaluation_dir / "results"
    synthetic_dir.mkdir(exist_ok=True)
    evaluation_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    # Step 1: Generate synthetic test data
    print("1. Generating synthetic test data...")
    generator = SyntheticDataGenerator(seed=42)
    test_data = generator.generate_evaluation_set(100)  # 100 test samples

    test_data_file = synthetic_dir / "test_data.jsonl"
    generator.save_dataset(test_data, str(test_data_file))
    print(f"   Generated {len(test_data)} test samples")

    # Step 1b: Generate large training dataset
    print("1b. Generating large training dataset...")
    training_data = generator.generate_dataset(1200, noise_level=0.1)  # 1200+ samples with noise
    training_data_file = synthetic_dir / "training_data.jsonl"
    generator.save_dataset(training_data, str(training_data_file))
    print(f"   Generated {len(training_data)} training samples")

    # Step 2: Simulate predictions (using ground truth as predictions for testing)
    print("2. Simulating predictions...")
    # In real scenario, this would be actual model predictions
    predictions = test_data.copy()  # Using ground truth as predictions for demo

    predictions_file = synthetic_dir / "predictions.jsonl"
    generator.save_dataset(predictions, str(predictions_file))
    print(f"   Created {len(predictions)} predictions")

    # Step 3: Run evaluation
    print("3. Running evaluation...")
    evaluator = ReceiptEvaluator(str(predictions_file), str(test_data_file))
    report = evaluator.evaluate()

    report_file = results_dir / "evaluation_report.json"
    evaluator.save_report(report, str(report_file))
    print(f"   Overall score: {report['overall_score']:.3f}")
    # Step 4: Run regression check
    print("4. Running regression check...")
    runner = RegressionRunner(str(test_data_file), str(results_dir))
    regression_result = runner.run_regression_test(predictions, "regression_test")

    if regression_result['regression_check']['has_regression']:
        print("   ❌ REGRESSION DETECTED!")
        print(f"   {regression_result['regression_check']['message']}")
        for field, change in regression_result['regression_check']['changes'].items():
            print(f"   {field}: {change['baseline']:.3f} → {change['current']:.3f}")
        return 1
    else:
        print("   ✅ No regression detected")

    # Step 5: Print summary
    print("\n5. Test Summary:")
    print(f"   Overall Score: {report['overall_score']:.3f}")
    print("   Field Scores:")
    for field, score in report['field_scores'].items():
        print("25s")

    print(f"\n   Results saved to: {results_dir}")
    print(f"   - Evaluation report: evaluation_report.json")
    print(f"   - Regression results: regression_test_*.json")

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)