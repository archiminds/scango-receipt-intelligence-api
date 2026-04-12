# Evaluation Framework

This directory contains the evaluation and regression testing framework for the ScanGo Receipt Intelligence API.

## Components

### evaluator.py
Main evaluation engine that compares predictions against ground truth.

**Key Features:**
- Load predictions and ground truth from JSONL files
- Comprehensive field-by-field accuracy calculation
- Error analysis and common failure detection
- Confidence interval calculation
- Detailed reporting and summary printing

### metrics.py
Evaluation metrics and scoring algorithms.

**Metrics:**
- **Text Similarity**: Sequence matching for vendor/category fields
- **Amount Accuracy**: Multi-tier precision (exact, ±1¢, ±10¢, ±$1)
- **Date Parsing**: Flexible date matching (exact, same day, same month)
- **Item Extraction**: Combined name+price similarity scoring
- **Overall Scoring**: Weighted average across all fields

### regression_runner.py
Regression testing framework for continuous performance monitoring.

**Features:**
- Baseline management (creation, updates, comparison)
- Regression detection with configurable thresholds
- Batch testing support
- Historical result tracking
- Comprehensive regression reports

## Usage Examples

### Basic Evaluation
```python
from evaluation.evaluator import ReceiptEvaluator

# Load and evaluate
evaluator = ReceiptEvaluator('predictions.jsonl', 'ground_truth.jsonl')
report = evaluator.evaluate()

# Print summary
evaluator.print_summary(report)

# Save detailed report
evaluator.save_report(report, 'evaluation_report.json')
```

### Regression Testing
```python
from evaluation.regression_runner import RegressionRunner

# Initialize runner
runner = RegressionRunner('test_data.jsonl', 'results/')

# Run regression test
result = runner.run_regression_test(predictions, 'daily_test')

# Check for regressions
if result['regression_check']['has_regression']:
    print("REGRESSION DETECTED!")
    print(result['regression_check']['message'])
```

### CLI Usage
```bash
# Evaluate predictions
python3 -m evaluation.evaluator --predictions predictions.jsonl --ground-truth ground_truth.jsonl --output report.json

# Run regression tests
python3 run_regression_tests.py
```

## Metrics Details

### Field Weights (Default)
- vendor: 0.1
- receipt_date: 0.1
- total_amount: 0.25
- gst_amount: 0.15
- subtotal_amount: 0.1
- items: 0.15
- currency: 0.05
- category: 0.1

### Accuracy Scoring
- **1.0**: Perfect match
- **0.9**: Within 1 cent (amounts) or same day (dates)
- **0.5**: Within 10 cents or same month
- **0.1**: Within $1
- **0.0**: No match

### Confidence Intervals
- 95% confidence intervals calculated for all fields
- Used to determine statistical significance of changes
- Helps distinguish real regressions from noise

## Regression Detection

### Thresholds
- **Overall Score**: 5% drop triggers regression
- **Field Scores**: Individual field 5% drops tracked
- **Configurable**: Thresholds can be adjusted per use case

### Baseline Management
- **Automatic Creation**: First run creates baseline
- **Manual Updates**: `update_baseline()` method for planned changes
- **Timestamp Tracking**: All results timestamped for historical analysis

## Output Formats

### Evaluation Report
```json
{
  "overall_score": 0.923,
  "field_scores": {
    "vendor": 0.95,
    "receipt_date": 0.89,
    "total_amount": 0.98,
    "gst_amount": 0.91,
    "subtotal_amount": 0.94,
    "items": 0.87,
    "currency": 1.0,
    "category": 0.88
  },
  "individual_scores": [...],
  "total_samples": 100,
  "error_analysis": {
    "field_error_rates": {...},
    "common_failures": [...]
  },
  "confidence_intervals": {...}
}
```

### Regression Report
```json
{
  "results": {...},
  "regression_check": {
    "has_regression": false,
    "message": "No regression detected",
    "changes": {}
  },
  "result_file": "results/test_1640995200.json"
}
```

## Integration

### With CI/CD
```yaml
# GitHub Actions example
- name: Run Regression Tests
  run: |
    python3 run_regression_tests.py
    if [ $? -ne 0 ]; then
      echo "Regression detected!"
      exit 1
    fi
```

### With Model Training
```python
# Evaluate model predictions
predictions = model.predict(test_data)
runner = RegressionRunner('test_data.jsonl')
result = runner.run_regression_test(predictions, 'model_v2')

if result['regression_check']['has_regression']:
    print("Model performance regressed!")
    # Trigger rollback or investigation
```

## Best Practices

1. **Baseline Updates**: Only update baselines for intentional performance changes
2. **Threshold Tuning**: Adjust regression thresholds based on your accuracy requirements
3. **Regular Testing**: Run regression tests with each deployment
4. **Error Analysis**: Review common failures to guide improvements
5. **Confidence Intervals**: Use confidence intervals to avoid false positives

## Performance

- **Evaluation Speed**: ~1000 samples/second
- **Memory Usage**: < 50MB for large datasets
- **Storage**: ~10KB per evaluation report
- **Scalability**: Handles datasets with 10,000+ samples