"""Tests for evaluation regression baseline behavior.

These tests use temporary files so baseline creation and update logic can be
verified without modifying the repository's real evaluation results.
"""

import pytest
import json
from evaluation.regression_runner import RegressionRunner
from pathlib import Path


class TestRegressionRunner:
    """Regression tests for the evaluation system."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for test files."""
        return tmp_path

    @pytest.fixture
    def sample_test_data(self, temp_dir):
        """Create sample test data file."""
        test_data = [
            {
                "receipt_text": "STARBUCKS\nTotal: $5.50",
                "expected_output": {
                    "vendor": "STARBUCKS",
                    "total_amount": 5.50,
                    "category": "Food"
                }
            }
        ]

        test_file = temp_dir / "test_data.jsonl"
        with open(test_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')

        return test_file

    @pytest.fixture
    def sample_predictions(self):
        """Create sample predictions."""
        return [
            {
                "expected_output": {
                    "vendor": "STARBUCKS",
                    "total_amount": 5.50,
                    "category": "Food"
                }
            }
        ]

    def test_regression_runner_initialization(self, sample_test_data, temp_dir):
        """Test regression runner initialization."""
        runner = RegressionRunner(str(sample_test_data), str(temp_dir / "results"))
        assert runner.test_data_path == sample_test_data
        assert runner.results_dir == temp_dir / "results"

    def test_run_regression_test(self, sample_test_data, sample_predictions, temp_dir):
        """Test running a regression test."""
        runner = RegressionRunner(str(sample_test_data), str(temp_dir / "results"))

        result = runner.run_regression_test(sample_predictions, "test_run")

        assert 'results' in result
        assert 'regression_check' in result
        assert 'result_file' in result
        assert result['results']['total_samples'] == 1

    def test_regression_check_no_baseline(self, sample_test_data, sample_predictions, temp_dir):
        """Test regression check when no baseline exists."""
        runner = RegressionRunner(str(sample_test_data), str(temp_dir / "results"))

        result = runner.run_regression_test(sample_predictions, "new_test")

        regression_check = result['regression_check']
        assert not regression_check['has_regression']
        assert 'New baseline created' in regression_check['message']

    def test_update_baseline(self, sample_test_data, sample_predictions, temp_dir):
        """Test baseline update functionality."""
        runner = RegressionRunner(str(sample_test_data), str(temp_dir / "results"))

        # Run test to create result file
        runner.run_regression_test(sample_predictions, "update_test")

        # Update baseline
        runner.update_baseline("update_test")

        # Check baseline was created
        baseline_file = temp_dir / "results" / "update_test_baseline.json"
        assert baseline_file.exists()
