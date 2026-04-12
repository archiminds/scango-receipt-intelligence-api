from typing import Dict, List, Any
import random
from synthetic.templates import ReceiptTemplates


class ScenarioDefinitions:
    """Defines various receipt scenarios for synthetic data generation."""

    SCENARIOS = {
        'simple_food': {
            'category': 'Food',
            'item_count': 1,
            'complexity': 'low'
        },
        'complex_food': {
            'category': 'Food',
            'item_count': (2, 5),
            'complexity': 'high'
        },
        'car_fuel': {
            'category': 'Car',
            'item_count': 1,
            'complexity': 'low'
        },
        'travel_booking': {
            'category': 'Travel',
            'item_count': 1,
            'complexity': 'medium'
        },
        'utilities_bill': {
            'category': 'Utilities',
            'item_count': 1,
            'complexity': 'low'
        },
        'office_supplies': {
            'category': 'Office Supplies',
            'item_count': (1, 3),
            'complexity': 'medium'
        },
        'staff_amenities': {
            'category': 'Staff Amenities',
            'item_count': (2, 4),
            'complexity': 'medium'
        },
        'equipment_purchase': {
            'category': 'Equipment',
            'item_count': 1,
            'complexity': 'high'
        },
        'accounting_service': {
            'category': 'Accounting Fee',
            'item_count': 1,
            'complexity': 'low'
        },
        'operational_cost': {
            'category': 'Operational Cost',
            'item_count': 1,
            'complexity': 'medium'
        }
    }

    AMBIGUOUS_SCENARIOS = {
        'amazon_office': {
            'category': 'Office Supplies',
            'vendor': 'Amazon',
            'items': ['Batteries', 'Cable', 'Paper'],
            'context': 'office'
        },
        'amazon_food': {
            'category': 'Staff Amenities',
            'vendor': 'Amazon',
            'items': ['Snacks', 'Coffee', 'Pantry Items'],
            'context': 'food'
        },
        'espresso_food': {
            'category': 'Food',
            'vendor': 'Espresso',
            'items': ['Coffee', 'Pastry'],
            'context': 'beverage'
        },
        'espresso_amenities': {
            'category': 'Staff Amenities',
            'vendor': 'Espresso',
            'items': ['Coffee Beans', 'Filters'],
            'context': 'pantry'
        },
        'parking_car': {
            'category': 'Car',
            'vendor': 'Point Parking',
            'items': ['Parking Fee'],
            'context': 'vehicle'
        },
        'parking_travel': {
            'category': 'Travel',
            'vendor': 'Airport Parking',
            'items': ['Parking Fee'],
            'context': 'travel'
        }
    }

    @staticmethod
    def get_scenario_config(scenario_name: str) -> Dict[str, Any]:
        """Get configuration for a specific scenario."""
        return ScenarioDefinitions.SCENARIOS.get(scenario_name, ScenarioDefinitions.SCENARIOS['simple_food'])

    @staticmethod
    def get_all_scenarios() -> List[str]:
        """Get list of all available scenarios."""
        return list(ScenarioDefinitions.SCENARIOS.keys())

    @staticmethod
    def get_ambiguous_scenarios() -> List[str]:
        """Get list of ambiguous scenarios."""
        return list(ScenarioDefinitions.AMBIGUOUS_SCENARIOS.keys())

    @staticmethod
    def generate_scenario_data(scenario_name: str) -> Dict[str, Any]:
        """Generate data for a specific scenario."""
        if scenario_name in ScenarioDefinitions.AMBIGUOUS_SCENARIOS:
            scenario_data = ScenarioDefinitions.AMBIGUOUS_SCENARIOS[scenario_name].copy()
            
            # Convert string items to proper item format
            if 'items' in scenario_data and isinstance(scenario_data['items'], list):
                items = []
                for item_name in scenario_data['items']:
                    # Get a random price for the item
                    category = scenario_data['category']
                    item_templates = ReceiptTemplates.ITEMS.get(category, [{'name': 'Generic Item', 'price_range': (10, 50)}])
                    price_range = item_templates[0]['price_range'] if item_templates else (10, 50)
                    price = round(random.uniform(*price_range), 2)
                    items.append({'name': item_name, 'price': price})
                scenario_data['items'] = items
            
            # Calculate totals
            subtotal = sum(item['price'] for item in scenario_data['items'])
            gst = round(subtotal * 0.1, 2)  # 10% GST
            total = round(subtotal + gst, 2)
            
            # Add calculated fields
            scenario_data.update({
                'subtotal': subtotal,
                'gst': gst,
                'total': total,
                'date': ReceiptTemplates.generate_random_date(),
                'complexity': 'high'  # Ambiguous scenarios are complex
            })
            
            return scenario_data

        config = ScenarioDefinitions.get_scenario_config(scenario_name)

        # Generate item count
        if isinstance(config['item_count'], tuple):
            item_count = random.randint(*config['item_count'])
        else:
            item_count = config['item_count']

        # Generate items
        items = ReceiptTemplates.get_random_items(config['category'], item_count)

        # Calculate totals
        subtotal = sum(item['price'] for item in items)
        gst = round(subtotal * 0.1, 2)  # 10% GST
        total = round(subtotal + gst, 2)

        # Get vendor
        vendor = ReceiptTemplates.get_random_vendor(config['category'])

        # Generate date
        date = ReceiptTemplates.generate_random_date()

        return {
            'category': config['category'],
            'vendor': vendor,
            'items': items,
            'subtotal': subtotal,
            'gst': gst,
            'total': total,
            'date': date,
            'complexity': config['complexity']
        }