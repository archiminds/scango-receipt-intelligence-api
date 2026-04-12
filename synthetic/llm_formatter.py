import json
from typing import Dict, List, Any
from synthetic.templates import ReceiptTemplates
from synthetic.noise import NoiseGenerator


class LLMFormatter:
    """Formats synthetic data for LLM training and evaluation."""

    @staticmethod
    def format_for_training(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format receipt data for LLM training."""
        receipt_text = ReceiptTemplates.generate_receipt_text(
            receipt_data['vendor'],
            receipt_data['category'],
            receipt_data['items'],
            receipt_data['total'],
            receipt_data['gst'],
            receipt_data['date']
        )

        # Add noise for realism
        noisy_text = NoiseGenerator.add_ocr_noise(receipt_text, noise_level=0.05)
        noisy_text = NoiseGenerator.add_layout_noise(noisy_text)

        return {
            'input': noisy_text,
            'output': {
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
                'complexity': receipt_data.get('complexity', 'medium'),
                'noise_level': 0.05
            }
        }

    @staticmethod
    def format_for_evaluation(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format receipt data for evaluation."""
        training_format = LLMFormatter.format_for_training(receipt_data)

        return {
            'receipt_text': training_format['input'],
            'expected_output': training_format['output'],
            'evaluation_criteria': {
                'vendor_accuracy': True,
                'date_parsing': True,
                'amount_accuracy': True,
                'item_extraction': True,
                'categorization': True
            }
        }

    @staticmethod
    def create_prompt_template(receipt_text: str) -> str:
        """Create a prompt template for LLM parsing."""
        return f"""
Parse the following receipt text and extract structured information.
Return ONLY a valid JSON object with the following structure:
{{
    "vendor": "store name or null",
    "receipt_date": "YYYY-MM-DD or null",
    "items": [
        {{
            "name": "item name",
            "quantity": 1,
            "unit_price": 10.50,
            "total_price": 10.50
        }}
    ],
    "subtotal_amount": 10.50,
    "total_amount": 11.55,
    "gst_amount": 1.05,
    "currency": "AUD"
}}

Rules:
- Extract vendor name from the receipt
- Parse date in YYYY-MM-DD format
- Extract all items with their prices
- Calculate amounts as decimal numbers
- If GST is not explicitly mentioned, leave gst_amount as null
- Be precise with numbers and dates

Receipt text:
{receipt_text}
"""

    @staticmethod
    def create_categorization_prompt(receipt_text: str, vendor: str = None, items: List[Dict] = None) -> str:
        """Create a prompt template for categorization."""
        categories = [
            "Car", "Travel", "Utilities", "Equipment", "Food",
            "Staff Amenities", "Office Supplies", "Accounting Fee", "Operational Cost", "Unclassified"
        ]

        context = ""
        if vendor:
            context += f"Vendor: {vendor}\n"
        if items:
            item_names = [item.get('name', '') for item in items]
            context += f"Items: {', '.join(item_names)}\n"

        return f"""
Categorize this receipt into one of the following categories:
{', '.join(categories)}

{context}
Receipt text:
{receipt_text}

Return only the category name and a brief reason.
"""

    @staticmethod
    def export_dataset(dataset: List[Dict[str, Any]], filename: str, format_type: str = 'jsonl'):
        """Export dataset to file."""
        if format_type == 'jsonl':
            with open(filename, 'w') as f:
                for item in dataset:
                    f.write(json.dumps(item) + '\n')
        elif format_type == 'json':
            with open(filename, 'w') as f:
                json.dump(dataset, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    @staticmethod
    def load_dataset(filename: str) -> List[Dict[str, Any]]:
        """Load dataset from file."""
        dataset = []
        with open(filename, 'r') as f:
            if filename.endswith('.jsonl'):
                for line in f:
                    dataset.append(json.loads(line.strip()))
            elif filename.endswith('.json'):
                dataset = json.load(f)

        return dataset