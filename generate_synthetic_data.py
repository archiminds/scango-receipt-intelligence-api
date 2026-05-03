#!/usr/bin/env python3
"""
Generate large synthetic receipt dataset for training and evaluation.
Creates 1000+ synthetic receipts with OCR noise injection and golden dataset support.

Use this when refreshing broad local datasets. For the smaller deployed API
smoke-test flow, use scripts/generate_custom_dataset.py instead.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from synthetic.generator import SyntheticDataGenerator


def main():
    """Generate comprehensive synthetic dataset."""
    print("Generating comprehensive synthetic receipt dataset...")

    # Create directories
    synthetic_dir = project_root / "synthetic"
    synthetic_dir.mkdir(exist_ok=True)

    generator = SyntheticDataGenerator(seed=42)

    # Generate training dataset (1000+ samples)
    print("1. Generating training dataset (1200 samples)...")
    training_data = generator.generate_dataset(
        size=1200,
        scenarios=None,  # All scenarios
        include_ambiguous=True,
        noise_level=0.1  # OCR noise
    )

    training_file = synthetic_dir / "training_dataset.jsonl"
    generator.save_dataset(training_data, str(training_file), format_type='jsonl')
    print(f"   ✓ Saved {len(training_data)} training samples to {training_file}")

    # Generate evaluation dataset (200 samples, clean)
    print("2. Generating evaluation dataset (200 samples)...")
    eval_data = generator.generate_evaluation_set(200)

    eval_file = synthetic_dir / "evaluation_dataset.jsonl"
    generator.save_dataset(eval_data, str(eval_file), format_type='jsonl')
    print(f"   ✓ Saved {len(eval_data)} evaluation samples to {eval_file}")

    # Generate golden dataset (100 samples, perfect quality). This is useful
    # when debugging parser behavior without OCR noise as a confounding factor.
    print("3. Generating golden dataset (100 samples)...")
    golden_data = generator.generate_dataset(
        size=100,
        scenarios=None,
        include_ambiguous=False,
        noise_level=0.0  # No noise for golden dataset
    )

    golden_file = synthetic_dir / "golden_dataset.jsonl"
    generator.save_dataset(golden_data, str(golden_file), format_type='jsonl')
    print(f"   ✓ Saved {len(golden_data)} golden samples to {golden_file}")

    # Generate high-noise dataset for robustness testing
    print("4. Generating high-noise dataset (300 samples)...")
    noisy_data = generator.generate_dataset(
        size=300,
        scenarios=None,
        include_ambiguous=True,
        noise_level=0.3  # High OCR noise
    )

    noisy_file = synthetic_dir / "noisy_dataset.jsonl"
    generator.save_dataset(noisy_data, str(noisy_file), format_type='jsonl')
    print(f"   ✓ Saved {len(noisy_data)} noisy samples to {noisy_file}")

    # Summary
    total_samples = len(training_data) + len(eval_data) + len(golden_data) + len(noisy_data)
    print("\nDataset Generation Complete!")
    print(f"Total samples generated: {total_samples}")
    print(f"- Training: {len(training_data)} samples (with OCR noise)")
    print(f"- Evaluation: {len(eval_data)} samples (clean)")
    print(f"- Golden: {len(golden_data)} samples (perfect quality)")
    print(f"- Noisy: {len(noisy_data)} samples (high noise)")

    print("\nFiles created:")
    print(f"- {training_file}")
    print(f"- {eval_file}")
    print(f"- {golden_file}")
    print(f"- {noisy_file}")

    print("\nNext steps:")
    print("- Use training_dataset.jsonl for model training")
    print("- Use evaluation_dataset.jsonl for performance evaluation")
    print("- Use golden_dataset.jsonl as reference for perfect parsing")
    print("- Use noisy_dataset.jsonl to test OCR robustness")


if __name__ == "__main__":
    main()
