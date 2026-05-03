#!/usr/bin/env python3
"""Generate a small synthetic dataset plus ground-truth outputs.

This script is intended for quick deployed-API accuracy checks. It writes both
the parser input samples and the ground truth that evaluation.evaluator uses.
"""

import json
import sys
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from synthetic.generator import SyntheticDataGenerator


def main():
    output_dir = Path("synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = SyntheticDataGenerator(seed=42)
    # Keep the custom dataset intentionally small so a live API prediction run
    # is fast and does not create unnecessary Bedrock cost.
    dataset = generator.generate_dataset(size=10)

    dataset_path = output_dir / "custom_dataset.jsonl"
    generator.save_dataset(dataset, str(dataset_path))

    ground_truth_path = output_dir / "custom_ground_truth.jsonl"
    with ground_truth_path.open("w") as f:
        for entry in dataset:
            # Ground truth files contain only expected outputs. request_id is
            # added so reports can correlate results even when samples move.
            gt = entry["expected_output"].copy()
            gt["request_id"] = (
                entry.get("request_id")
                or entry.get("metadata", {}).get("id")
                or str(uuid4())
            )
            f.write(json.dumps(gt) + "\n")

    print(f"Saved synthetic dataset to {dataset_path}")
    print(f"Saved ground truth to {ground_truth_path}")


if __name__ == "__main__":
    main()
