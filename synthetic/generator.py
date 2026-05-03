"""High-level synthetic receipt dataset generator.

This module combines scenario definitions, receipt templates, OCR noise, and
formatter utilities to create repeatable datasets for training, evaluation, and
regression testing.
"""

import random
import json
from typing import List, Dict, Any, Optional
from synthetic.templates import ReceiptTemplates
from synthetic.noise import NoiseGenerator
from synthetic.scenario_definitions import ScenarioDefinitions
from synthetic.llm_formatter import LLMFormatter


class SyntheticDataGenerator:
    """Main generator for synthetic receipt data."""

    def __init__(self, seed: Optional[int] = None):
        if seed:
            # A seed makes generated datasets reproducible, which is critical
            # when comparing parser accuracy before and after code changes.
            random.seed(seed)

    def generate_dataset(self, size: int = 1000,
                        scenarios: Optional[List[str]] = None,
                        include_ambiguous: bool = True,
                        noise_level: float = 0.1) -> List[Dict[str, Any]]:
        """Generate a dataset of synthetic receipts."""
        dataset = []

        if not scenarios:
            scenarios = ScenarioDefinitions.get_all_scenarios()

        if include_ambiguous:
            # Ambiguous scenarios exercise category rules where the same vendor
            # or keyword could reasonably map to more than one expense class.
            scenarios.extend(ScenarioDefinitions.get_ambiguous_scenarios())

        for _ in range(size):
            # Select a scenario first, then ask ScenarioDefinitions to fill in
            # realistic vendor, item, amount, GST, and date values.
            scenario = random.choice(scenarios)
            receipt_data = ScenarioDefinitions.generate_scenario_data(scenario)

            # Generate clean receipt text before adding synthetic OCR noise so
            # we can keep both the parser input and the expected answer.
            receipt_text = ReceiptTemplates.generate_receipt_text(
                receipt_data['vendor'],
                receipt_data['category'],
                receipt_data['items'],
                receipt_data['total'],
                receipt_data['gst'],
                receipt_data['date']
            )

            # Ensure a clean ISO date line is present for downstream evaluation.
            if receipt_data.get('date'):
                iso_date_line = f"Date: {receipt_data['date']}"
                receipt_text = f"{iso_date_line}\n{receipt_text}"

            # Add OCR/layout noise after generating the golden text. The noisy
            # text simulates what a mobile OCR layer might send to the API.
            noisy_text = NoiseGenerator.add_ocr_noise(receipt_text, noise_level)
            noisy_text = NoiseGenerator.add_layout_noise(noisy_text)

            # Store both input and expected output in each row so the evaluator
            # can score predictions field by field.
            data_point = {
                'receipt_text': noisy_text,
                'clean_text': receipt_text,
                'expected_output': {
                    'vendor': receipt_data['vendor'],
                    'receipt_date': receipt_data['date'],
                    'items': receipt_data['items'],
                    'subtotal_amount': receipt_data['subtotal'],
                    'total_amount': receipt_data['total'],
                    'gst_amount': receipt_data['gst'],
                    'currency': 'AUD',
                    'category': receipt_data['category']
                },
                'metadata': {
                    'scenario': scenario,
                    'complexity': receipt_data.get('complexity', 'medium'),
                    'noise_level': noise_level,
                    'has_gst': True
                }
            }

            dataset.append(data_point)

        return dataset

    def generate_training_examples(self, size: int = 1000) -> List[Dict[str, Any]]:
        """Generate examples formatted for LLM training."""
        dataset = self.generate_dataset(size)
        training_examples = []

        for data_point in dataset:
            example = LLMFormatter.format_for_training({
                'vendor': data_point['expected_output']['vendor'],
                'category': data_point['expected_output']['category'],
                'items': data_point['expected_output']['items'],
                'total': data_point['expected_output']['total_amount'],
                'gst': data_point['expected_output']['gst_amount'],
                'subtotal': data_point['expected_output']['subtotal_amount'],
                'date': data_point['expected_output']['receipt_date'],
                'complexity': data_point['metadata']['complexity']
            })
            training_examples.append(example)

        return training_examples

    def generate_evaluation_set(self, size: int = 100) -> List[Dict[str, Any]]:
        """Generate evaluation dataset."""
        dataset = self.generate_dataset(size, include_ambiguous=True)
        evaluation_set = []

        for data_point in dataset:
            eval_point = LLMFormatter.format_for_evaluation({
                'vendor': data_point['expected_output']['vendor'],
                'category': data_point['expected_output']['category'],
                'items': data_point['expected_output']['items'],
                'total': data_point['expected_output']['total_amount'],
                'gst': data_point['expected_output']['gst_amount'],
                'subtotal': data_point['expected_output']['subtotal_amount'],
                'date': data_point['expected_output']['receipt_date'],
                'complexity': data_point['metadata']['complexity']
            })
            evaluation_set.append(eval_point)

        return evaluation_set

    def save_dataset(self, dataset: List[Dict[str, Any]], filename: str,
                    format_type: str = 'jsonl'):
        """Save dataset to file."""
        LLMFormatter.export_dataset(dataset, filename, format_type)

    def load_dataset(self, filename: str) -> List[Dict[str, Any]]:
        """Load dataset from file."""
        return LLMFormatter.load_dataset(filename)


# CLI interface for generation
if __name__ == "__main__":
    generator = SyntheticDataGenerator(seed=42)

    # Generate training data
    print("Generating training dataset...")
    training_data = generator.generate_training_examples(1000)
    generator.save_dataset(training_data, 'synthetic/training_data.jsonl')
    print(f"Generated {len(training_data)} training examples")

    # Generate evaluation data
    print("Generating evaluation dataset...")
    eval_data = generator.generate_evaluation_set(100)
    generator.save_dataset(eval_data, 'synthetic/evaluation_data.jsonl')
    print(f"Generated {len(eval_data)} evaluation examples")

    print("Synthetic data generation complete!")
