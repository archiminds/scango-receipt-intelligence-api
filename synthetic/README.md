# Synthetic Data and Evaluation Framework

This directory contains the synthetic data generation and evaluation framework for the ScanGo Receipt Intelligence API.

## Overview

The framework provides:
- **1000+ synthetic receipts** with realistic OCR noise injection
- **Golden dataset support** for perfect quality reference data
- **Comprehensive evaluator** with detailed metrics
- **Regression runner** for continuous performance monitoring

## Directory Structure

```
synthetic/
├── generator.py          # Main synthetic data generator
├── templates.py          # Receipt templates and vendor data
├── noise.py             # OCR noise injection utilities
├── scenario_definitions.py  # Receipt scenarios and categories
├── llm_formatter.py     # Data formatting for LLM training/evaluation
├── training_dataset.jsonl    # 1200 training samples with OCR noise
├── evaluation_dataset.jsonl  # 200 clean evaluation samples
├── golden_dataset.jsonl      # 100 perfect quality samples
└── noisy_dataset.jsonl       # 300 high-noise robustness samples

evaluation/
├── evaluator.py         # Receipt parsing evaluator
├── metrics.py          # Evaluation metrics and scoring
├── regression_runner.py # Regression testing framework
└── results/            # Evaluation results and baselines
```

## Synthetic Data Generation

### Features
- **OCR Noise Injection**: Character substitutions, missing/extra characters, layout noise
- **Realistic Scenarios**: 10+ receipt categories with vendor-specific templates
- **GST Calculation**: Automatic 10% GST calculation (Australian standard)
- **Hybrid Categorization**: Rules + AI approach with confidence thresholds
- **Ambiguous Cases**: Edge cases for testing categorization robustness

### Categories
- Car (Fuel, Car Wash, Oil Change)
- Travel (Flights, Taxis, Hotels)
- Utilities (Electricity, Mobile, Internet)
- Equipment (Laptops, Monitors, Keyboards)
- Food (Coffee, Lunch, Pizza)
- Staff Amenities (Snacks, Coffee, Pantry)
- Office Supplies (Paper, Pens, Notebooks)
- Accounting Fee (Monthly Accounting, Tax Prep)
- Operational Cost (Software, Cloud Hosting)

### Usage

Generate comprehensive dataset:
```bash
python3 generate_synthetic_data.py
```

Run regression tests:
```bash
python3 run_regression_tests.py
```

## Evaluation Framework

### Metrics
- **Field Accuracy**: Vendor, date, amounts, items, currency, category
- **Amount Precision**: Exact match, within 1¢, within 10¢, within $1
- **Date Parsing**: Exact, same day, same month
- **Item Matching**: Name similarity + price accuracy
- **Overall Score**: Weighted average across all fields

### Regression Testing
- **Baseline Management**: Automatic baseline creation and updates
- **Performance Monitoring**: Detects 5%+ performance drops
- **Confidence Intervals**: Statistical significance testing
- **Error Analysis**: Common failure patterns and field-specific issues

### Usage

Evaluate predictions against ground truth:
```python
from evaluation.evaluator import ReceiptEvaluator

evaluator = ReceiptEvaluator('predictions.jsonl', 'ground_truth.jsonl')
report = evaluator.evaluate()
evaluator.print_summary(report)
```

Run regression tests:
```python
from evaluation.regression_runner import RegressionRunner

runner = RegressionRunner('test_data.jsonl', 'results/')
result = runner.run_regression_test(predictions, 'test_name')
```

## Data Formats

### Training Format
```json
{
  "receipt_text": "noisy OCR text with errors",
  "clean_text": "perfect original text",
  "expected_output": {
    "vendor": "Store Name",
    "receipt_date": "2024-01-15",
    "items": [{"name": "Item", "price": 10.50}],
    "subtotal_amount": 10.50,
    "total_amount": 11.55,
    "gst_amount": 1.05,
    "currency": "AUD",
    "category": "Food"
  },
  "metadata": {
    "scenario": "simple_food",
    "complexity": "low",
    "noise_level": 0.1,
    "has_gst": true
  }
}
```

### Evaluation Format
```json
{
  "receipt_text": "receipt text for parsing",
  "expected_output": {...},
  "evaluation_criteria": {
    "vendor_accuracy": true,
    "date_parsing": true,
    "amount_accuracy": true,
    "item_extraction": true,
    "categorization": true
  }
}
```

## Key Features

### OCR Noise Types
- **Character Substitutions**: a→4, e→3, o→0, s→5, etc.
- **Missing Characters**: Random character removal
- **Extra Characters**: Random space/character insertion
- **Layout Noise**: Line breaks, spacing variations
- **Case Changes**: Random capitalization

### Evaluation Metrics
- **Text Similarity**: Sequence matcher for vendor/category
- **Amount Accuracy**: Decimal precision with tolerance bands
- **Date Accuracy**: ISO format parsing with flexibility
- **Item Matching**: Combined name+price similarity scoring

### Regression Detection
- **Threshold-based**: 5% performance drop triggers alert
- **Field-specific**: Individual field regression tracking
- **Statistical**: Confidence intervals for significance
- **Historical**: Baseline comparison with timestamp tracking

## Integration Notes

- **Lambda-safe**: All generation/evaluation runs outside Lambda
- **Deterministic**: Seed-based generation for reproducible results
- **Scalable**: Efficient generation of thousands of samples
- **Extensible**: Easy addition of new categories/scenarios

## Performance

- **Generation Speed**: ~1000 samples/minute
- **Evaluation Speed**: ~1000 samples/second
- **Memory Usage**: < 100MB for large datasets
- **Storage**: ~50KB per sample (JSONL format)