"""Product SKU generator for StormGuard.

Generates realistic product catalog with focus on hurricane-preparedness items
and everyday grocery staples.
"""

import pandas as pd
import numpy as np


# Product categories with hurricane-relevance scoring
PRODUCT_CATEGORIES = {
    'Water': {
        'hurricane_multiplier': 3.5,
        'base_price_range': (1, 8),
        'margin': 0.25,
        'shelf_life_days': 365,
        'weight_lbs_range': (1, 40)
    },
    'Batteries': {
        'hurricane_multiplier': 3.0,
        'base_price_range': (3, 25),
        'margin': 0.40,
        'shelf_life_days': 1825,
        'weight_lbs_range': (0.2, 1.5)
    },
    'Flashlights': {
        'hurricane_multiplier': 2.8,
        'base_price_range': (5, 50),
        'margin': 0.45,
        'shelf_life_days': 1825,
        'weight_lbs_range': (0.5, 2)
    },
    'Canned Goods': {
        'hurricane_multiplier': 2.5,
        'base_price_range': (1, 5),
        'margin': 0.30,
        'shelf_life_days': 730,
        'weight_lbs_range': (0.5, 3)
    },
    'First Aid': {
        'hurricane_multiplier': 2.2,
        'base_price_range': (5, 40),
        'margin': 0.50,
        'shelf_life_days': 1095,
        'weight_lbs_range': (0.3, 3)
    },
    'Generators': {
        'hurricane_multiplier': 2.0,
        'base_price_range': (300, 2000),
        'margin': 0.25,
        'shelf_life_days': 3650,
        'weight_lbs_range': (50, 200)
    },
    'Tarps & Covers': {
        'hurricane_multiplier': 2.3,
        'base_price_range': (10, 80),
        'margin': 0.40,
        'shelf_life_days': 1825,
        'weight_lbs_range': (2, 15)
    },
    'Bread': {
        'hurricane_multiplier': 1.8,
        'base_price_range': (2, 6),
        'margin': 0.35,
        'shelf_life_days': 7,
        'weight_lbs_range': (1, 2)
    },
    'Milk': {
        'hurricane_multiplier': 1.5,
        'base_price_range': (3, 7),
        'margin': 0.28,
        'shelf_life_days': 14,
        'weight_lbs_range': (2, 9)
    },
    'Snacks': {
        'hurricane_multiplier': 1.6,
        'base_price_range': (2, 8),
        'margin': 0.42,
        'shelf_life_days': 180,
        'weight_lbs_range': (0.5, 3)
    },
    'Beverages': {
        'hurricane_multiplier': 1.4,
        'base_price_range': (1, 12),
        'margin': 0.33,
        'shelf_life_days': 365,
        'weight_lbs_range': (1, 12)
    },
    'Frozen Foods': {
        'hurricane_multiplier': 0.6,
        'base_price_range': (3, 15),
        'margin': 0.35,
        'shelf_life_days': 180,
        'weight_lbs_range': (1, 5)
    },
    'Personal Care': {
        'hurricane_multiplier': 1.0,
        'base_price_range': (3, 30),
        'margin': 0.48,
        'shelf_life_days': 730,
        'weight_lbs_range': (0.3, 3)
    },
    'Cleaning Supplies': {
        'hurricane_multiplier': 1.3,
        'base_price_range': (3, 15),
        'margin': 0.40,
        'shelf_life_days': 1095,
        'weight_lbs_range': (1, 10)
    },
    'Pet Supplies': {
        'hurricane_multiplier': 1.4,
        'base_price_range': (5, 40),
        'margin': 0.38,
        'shelf_life_days': 365,
        'weight_lbs_range': (2, 30)
    },
}


class ProductGenerator(object):
    """Generates synthetic product catalog for retail simulation."""
    
    def __init__(self, num_products=200, seed=42):
        """Initialize product generator.
        
        Args:
            num_products: Total number of SKUs to generate
            seed: Random seed
        """
        self.num_products = num_products
        self.seed = seed
        np.random.seed(seed)
        
    def generate(self):
        """Generate complete product catalog.
        
        Returns:
            pandas.DataFrame with product attributes
        """
        products = []
        
        # Distribute products across categories
        category_counts = self._distribute_skus()
        
        sku_counter = 1
        for category, count in category_counts.items():
            category_config = PRODUCT_CATEGORIES[category]
            
            for _ in range(count):
                product = self._generate_single_product(
                    sku_counter,
                    category,
                    category_config
                )
                products.append(product)
                sku_counter += 1
        
        df = pd.DataFrame(products)
        
        # Add derived fields
        df['cost'] = df['base_price'] / (1 + df['margin'])
        df['gross_margin_pct'] = df['margin'] * 100
        
        return df
    
    def _generate_single_product(self, sku_id, category, config):
        """Generate a single product.
        
        Args:
            sku_id: Unique SKU number
            category: Product category name
            config: Category configuration dict
            
        Returns:
            dict with product attributes
        """
        min_price, max_price = config['base_price_range']
        base_price = round(np.random.uniform(min_price, max_price), 2)
        
        min_weight, max_weight = config['weight_lbs_range']
        weight = round(np.random.uniform(min_weight, max_weight), 2)
        
        # Add some variety to names
        variants = self._get_product_variants(category)
        variant_name = np.random.choice(variants)
        
        product = {
            'sku': 'SKU-{:04d}'.format(sku_id),
            'product_name': '{} - {}'.format(category, variant_name),
            'category': category,
            'base_price': base_price,
            'margin': config['margin'],
            'shelf_life_days': config['shelf_life_days'],
            'weight_lbs': weight,
            'hurricane_multiplier': config['hurricane_multiplier'],
            'unit_of_measure': self._get_uom(category),
            'min_order_qty': self._get_moq(category),
            'supplier_lead_time_days': self._get_lead_time(category),
            'perishable': config['shelf_life_days'] < 30
        }
        
        return product
    
    def _distribute_skus(self):
        """Distribute SKU count across categories.
        
        Hurricane-critical categories get more SKUs.
        
        Returns:
            dict mapping category to SKU count
        """
        weights = {}
        for cat, cfg in PRODUCT_CATEGORIES.items():
            # Weight by hurricane multiplier
            weights[cat] = cfg['hurricane_multiplier']
        
        total_weight = sum(weights.values())
        distribution = {}
        
        remaining = self.num_products
        for cat in sorted(weights.keys()):
            if remaining <= 0:
                break
            # Allocate proportionally but ensure minimum of 5 per category
            ratio = weights[cat] / total_weight
            count = max(5, int(self.num_products * ratio))
            count = min(count, remaining)
            distribution[cat] = count
            remaining -= count
        
        # Distribute any remainder
        if remaining > 0:
            for cat in distribution:
                if remaining <= 0:
                    break
                distribution[cat] += 1
                remaining -= 1
        
        return distribution
    
    def _get_product_variants(self, category):
        """Get realistic product variant names.
        
        Args:
            category: Product category
            
        Returns:
            list of variant names
        """
        variants = {
            'Water': ['24pk Bottles', '12pk Bottles', '6pk Gallon', 'Single Gallon', '40pk Bottles'],
            'Batteries': ['AA 8pk', 'AAA 8pk', 'D 4pk', 'C 4pk', '9V 2pk', 'AA 20pk'],
            'Flashlights': ['LED Handheld', 'Lantern', 'Headlamp', 'Tactical', 'Mini LED'],
            'Canned Goods': ['Soup', 'Vegetables', 'Beans', 'Fruit', 'Meat', 'Pasta'],
            'First Aid': ['Basic Kit', 'Premium Kit', 'Travel Kit', 'Bandages', 'Antiseptic'],
            'Generators': ['2000W Portable', '3500W Portable', '5000W', '7500W', 'Inverter 2000W'],
            'Tarps & Covers': ['8x10 Tarp', '10x12 Tarp', '20x20 Tarp', 'Sandbags 50pk', 'Plastic Sheeting'],
            'Bread': ['White Loaf', 'Wheat Loaf', 'Sourdough', 'Baguette', 'Rolls 12pk'],
            'Milk': ['Whole Gallon', '2% Gallon', 'Skim Gallon', 'Whole Half-Gallon', 'Almond Milk'],
            'Snacks': ['Chips', 'Crackers', 'Cookies', 'Granola Bars', 'Trail Mix', 'Nuts'],
            'Beverages': ['Soda 12pk', 'Juice Gallon', 'Sports Drink 8pk', 'Coffee 12oz', 'Tea Bags 100ct'],
            'Frozen Foods': ['Pizza', 'Vegetables', 'Ice Cream', 'Meals', 'Chicken'],
            'Personal Care': ['Shampoo', 'Soap', 'Toothpaste', 'Deodorant', 'Tissues'],
            'Cleaning Supplies': ['Bleach', 'Paper Towels', 'Toilet Paper', 'Dish Soap', 'Spray Cleaner'],
            'Pet Supplies': ['Dog Food 20lb', 'Cat Food 10lb', 'Pet Treats', 'Litter 25lb', 'Pet Bowls'],
        }
        return variants.get(category, ['Standard', 'Premium', 'Value'])
    
    def _get_uom(self, category):
        """Get unit of measure for category.
        
        Args:
            category: Product category
            
        Returns:
            str unit of measure
        """
        uom_map = {
            'Water': 'pack',
            'Batteries': 'pack',
            'Flashlights': 'each',
            'Generators': 'each',
            'Tarps & Covers': 'each',
        }
        return uom_map.get(category, 'each')
    
    def _get_moq(self, category):
        """Get minimum order quantity.
        
        Args:
            category: Product category
            
        Returns:
            int minimum order quantity
        """
        if category in ['Generators', 'Tarps & Covers']:
            return np.random.choice([1, 2, 5])
        else:
            return np.random.choice([6, 12, 24])
    
    def _get_lead_time(self, category):
        """Get supplier lead time in days.
        
        Args:
            category: Product category
            
        Returns:
            int lead time days
        """
        # Perishables have shorter lead times
        if category in ['Bread', 'Milk', 'Frozen Foods']:
            return np.random.randint(1, 3)
        elif category in ['Generators']:
            return np.random.randint(7, 21)
        else:
            return np.random.randint(3, 10)


def main():
    """Generate and save product data."""
    generator = ProductGenerator(num_products=200)
    products_df = generator.generate()
    
    output_path = 'data/output/products.csv'
    products_df.to_csv(output_path, index=False)
    print('Generated {} products -> {}'.format(len(products_df), output_path))
    print('\nTop hurricane-critical categories:')
    top_cats = products_df.nlargest(5, 'hurricane_multiplier')[['category', 'hurricane_multiplier']].drop_duplicates()
    print(top_cats)
    print('\nPrice distribution:')
    print(products_df['base_price'].describe())


if __name__ == '__main__':
    main()
