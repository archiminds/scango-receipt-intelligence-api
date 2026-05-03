"""Receipt text templates and category-specific vendor/item pools.

Templates produce realistic but deterministic-enough source receipts for the
synthetic generator. Scenario definitions choose categories and item counts;
this module supplies plausible names, prices, and rendered text.
"""

from typing import Dict, List, Any
import random
from datetime import datetime, timedelta


class ReceiptTemplates:
    """Templates for generating synthetic receipt data."""

    VENDORS = {
        'Car': ['BP', 'Ampol', 'Caltex', 'Shell', 'NRMA'],
        'Travel': ['Uber', 'Taxi Service', 'Singapore Airlines', '7-Eleven'],
        'Utilities': ['AGL', 'Optus', 'Telstra'],
        'Equipment': ['JB Hi-Fi', 'OfficeWorks'],
        'Food': ['Nandos', 'Domino\'s Pizza', 'Starbucks', 'McDonald\'s'],
        'Staff Amenities': ['Aldi', 'Coles', 'Woolworths'],
        'Office Supplies': ['Office Depot', 'Staples'],
        'Accounting Fee': ['Xero', 'MYOB'],
        'Operational Cost': ['Google Workspace', 'Microsoft 365', 'AWS']
    }

    ITEMS = {
        'Car': [
            {'name': 'Fuel', 'price_range': (50, 150)},
            {'name': 'Car Wash', 'price_range': (15, 30)},
            {'name': 'Oil Change', 'price_range': (80, 120)}
        ],
        'Travel': [
            {'name': 'Flight Ticket', 'price_range': (200, 800)},
            {'name': 'Taxi Fare', 'price_range': (20, 60)},
            {'name': 'Hotel Booking', 'price_range': (100, 300)}
        ],
        'Utilities': [
            {'name': 'Electricity Bill', 'price_range': (80, 200)},
            {'name': 'Mobile Plan', 'price_range': (40, 80)},
            {'name': 'Internet Service', 'price_range': (60, 120)}
        ],
        'Equipment': [
            {'name': 'Laptop', 'price_range': (1000, 2500)},
            {'name': 'Monitor', 'price_range': (200, 500)},
            {'name': 'Keyboard', 'price_range': (50, 150)}
        ],
        'Food': [
            {'name': 'Coffee', 'price_range': (3, 8)},
            {'name': 'Lunch Special', 'price_range': (12, 25)},
            {'name': 'Pizza', 'price_range': (15, 35)}
        ],
        'Staff Amenities': [
            {'name': 'Snacks Pack', 'price_range': (5, 15)},
            {'name': 'Coffee Beans', 'price_range': (8, 20)},
            {'name': 'Water Bottles', 'price_range': (2, 6)}
        ],
        'Office Supplies': [
            {'name': 'Printer Paper', 'price_range': (10, 25)},
            {'name': 'Pens', 'price_range': (3, 8)},
            {'name': 'Notebooks', 'price_range': (5, 12)}
        ],
        'Accounting Fee': [
            {'name': 'Monthly Accounting', 'price_range': (200, 500)},
            {'name': 'Tax Preparation', 'price_range': (300, 800)}
        ],
        'Operational Cost': [
            {'name': 'Software License', 'price_range': (50, 200)},
            {'name': 'Cloud Hosting', 'price_range': (100, 500)}
        ]
    }

    @staticmethod
    def generate_receipt_text(vendor: str, category: str, items: List[Dict[str, Any]],
                            total: float, gst: float, date: str) -> str:
        """Generate realistic receipt text."""
        # Keep the rendered format simple and consistent. Noise injection is
        # handled separately so we can also preserve this clean source text.
        lines = [
            vendor.upper(),
            f"Date: {date}",
            "",
            "Items:"
        ]

        for item in items:
            lines.append(f"{item['name']} - ${item['price']:.2f}")

        lines.extend([
            "",
            f"Subtotal: ${(total - gst):.2f}",
            f"GST: ${gst:.2f}",
            f"Total: ${total:.2f}",
            "",
            "Thank you for your business!"
        ])

        return "\n".join(lines)

    @staticmethod
    def get_random_vendor(category: str) -> str:
        """Get random vendor for category."""
        vendors = ReceiptTemplates.VENDORS.get(category, ['Generic Store'])
        return random.choice(vendors)

    @staticmethod
    def get_random_items(category: str, count: int = 1) -> List[Dict[str, Any]]:
        """Get random items for category."""
        items = ReceiptTemplates.ITEMS.get(category, [{'name': 'Generic Item', 'price_range': (10, 50)}])
        selected = random.sample(items, min(count, len(items)))

        result = []
        for item in selected:
            # Prices are rounded at generation time so expected outputs match
            # receipt text and evaluator comparisons.
            price = random.uniform(*item['price_range'])
            result.append({
                'name': item['name'],
                'price': round(price, 2)
            })

        return result

    @staticmethod
    def generate_random_date() -> str:
        """Generate random date within last year."""
        days_ago = random.randint(0, 365)
        date = datetime.now() - timedelta(days=days_ago)
        return date.strftime('%Y-%m-%d')
