"""Sales history generator for StormGuard.

Generates 2 years of synthetic sales data with realistic patterns:
- Seasonal trends
- Day-of-week effects
- Holiday spikes
- Hurricane Milton impact (Oct 2024)
- Store and product heterogeneity
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# Holiday impact dates and multipliers
HOLIDAYS = {
    '2023-07-04': 1.6,  # Independence Day
    '2023-11-23': 2.1,  # Thanksgiving
    '2023-12-25': 1.4,  # Christmas
    '2024-01-01': 1.3,  # New Year
    '2024-02-11': 1.5,  # Super Bowl Sunday
    '2024-05-27': 1.5,  # Memorial Day
    '2024-07-04': 1.6,  # Independence Day
    '2024-09-02': 1.4,  # Labor Day
    '2024-11-28': 2.1,  # Thanksgiving
    '2024-12-25': 1.4,  # Christmas
}

# Hurricane Milton impact window
MILTON_START = datetime(2024, 10, 7)
MILTON_PEAK = datetime(2024, 10, 9)
MILTON_END = datetime(2024, 10, 12)


class SalesGenerator(object):
    """Generates realistic sales transactions over 2-year period."""
    
    def __init__(self, stores_df, products_df, seed=42):
        """Initialize sales generator.
        
        Args:
            stores_df: DataFrame of stores
            products_df: DataFrame of products
            seed: Random seed
        """
        self.stores = stores_df
        self.products = products_df
        self.seed = seed
        np.random.seed(seed)
        
    def generate(self, start_date='2023-01-01', end_date='2024-12-31'):
        """Generate complete sales history.
        
        Args:
            start_date: Start date string
            end_date: End date string
            
        Returns:
            pandas.DataFrame with daily sales by store-SKU
        """
        print('Generating sales data from {} to {}...'.format(start_date, end_date))
        
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        sales_records = []
        
        # Pre-compute base velocities for each store-product combo
        velocities = self._compute_base_velocities()
        
        for date in date_range:
            if len(sales_records) % 36500 == 0:
                progress = len(sales_records) / (len(date_range) * len(self.stores) * 50)
                print('Progress: {:.1f}%'.format(progress * 100))
            
            day_sales = self._generate_day_sales(date, velocities)
            sales_records.extend(day_sales)
        
        print('Generated {} sales records'.format(len(sales_records)))
        df = pd.DataFrame(sales_records)
        return df
    
    def _generate_day_sales(self, date, velocities):
        """Generate sales for a single day across all stores.
        
        Args:
            date: datetime object
            velocities: Pre-computed velocity matrix
            
        Returns:
            list of sale dicts
        """
        day_sales = []
        
        # Compute global multipliers for this date
        seasonal_mult = self._seasonal_multiplier(date)
        dow_mult = self._day_of_week_multiplier(date)
        holiday_mult = self._holiday_multiplier(date)
        
        for _, store in self.stores.iterrows():
            store_id = store['store_id']
            
            # Each store sells ~30-50 unique SKUs per day (not all 200)
            num_skus_today = np.random.randint(30, 50)
            daily_skus = self.products.sample(n=num_skus_today)
            
            for _, product in daily_skus.iterrows():
                sku = product['sku']
                
                # Get base velocity for this store-sku pair
                base_qty = velocities.get((store_id, sku), np.random.poisson(5))
                
                # Apply multipliers
                qty = base_qty * seasonal_mult * dow_mult * holiday_mult
                
                # Hurricane impact for relevant products
                if MILTON_START <= date <= MILTON_END:
                    milton_mult = self._milton_multiplier(date, product, store)
                    qty *= milton_mult
                
                # Add noise
                qty = int(qty * np.random.uniform(0.8, 1.2))
                qty = max(0, qty)  # No negative sales
                
                if qty > 0:
                    sale = {
                        'date': date.strftime('%Y-%m-%d'),
                        'store_id': store_id,
                        'sku': sku,
                        'quantity_sold': qty,
                        'unit_price': product['base_price'],
                        'revenue': round(qty * product['base_price'], 2),
                        'cost': round(qty * product['base_price'] / (1 + product['margin']), 2)
                    }
                    day_sales.append(sale)
        
        return day_sales
    
    def _compute_base_velocities(self):
        """Pre-compute base sales velocity for store-SKU pairs.
        
        High-traffic stores sell more, popular categories sell more.
        
        Returns:
            dict mapping (store_id, sku) to base daily quantity
        """
        velocities = {}
        
        for _, store in self.stores.iterrows():
            # Store traffic affects all products
            traffic_factor = store['daily_traffic'] / 2000.0
            
            for _, product in self.products.iterrows():
                # Category popularity
                category_base = {
                    'Water': 15,
                    'Batteries': 8,
                    'Flashlights': 5,
                    'Canned Goods': 12,
                    'First Aid': 6,
                    'Generators': 1,
                    'Tarps & Covers': 3,
                    'Bread': 20,
                    'Milk': 18,
                    'Snacks': 25,
                    'Beverages': 22,
                    'Frozen Foods': 15,
                    'Personal Care': 10,
                    'Cleaning Supplies': 12,
                    'Pet Supplies': 8,
                }
                
                base = category_base.get(product['category'], 10)
                velocity = int(base * traffic_factor * np.random.uniform(0.5, 1.5))
                velocity = max(1, velocity)
                
                velocities[(store['store_id'], product['sku'])] = velocity
        
        return velocities
    
    def _seasonal_multiplier(self, date):
        """Calculate seasonal demand multiplier.
        
        Summer: higher drinks/water
        Winter: higher canned goods/comfort foods
        
        Args:
            date: datetime object
            
        Returns:
            float multiplier
        """
        month = date.month
        # Sine wave with peak in summer (July)
        return 1.0 + 0.2 * np.sin((month - 1) * np.pi / 6.0)
    
    def _day_of_week_multiplier(self, date):
        """Calculate day-of-week multiplier.
        
        Weekends are busier than weekdays.
        
        Args:
            date: datetime object
            
        Returns:
            float multiplier
        """
        if date.weekday() >= 5:  # Saturday=5, Sunday=6
            return 1.35
        else:
            return 1.0
    
    def _holiday_multiplier(self, date):
        """Calculate holiday multiplier.
        
        Args:
            date: datetime object
            
        Returns:
            float multiplier
        """
        date_str = date.strftime('%Y-%m-%d')
        return HOLIDAYS.get(date_str, 1.0)
    
    def _milton_multiplier(self, date, product, store):
        """Calculate Hurricane Milton impact multiplier.
        
        Varies by:
        - Product hurricane-relevance
        - Proximity to landfall (coastal stores hit harder)
        - Days until impact
        
        Args:
            date: datetime object
            product: product Series
            store: store Series
            
        Returns:
            float multiplier
        """
        if date < MILTON_START or date > MILTON_END:
            return 1.0
        
        # Coastal stores panic-buy more
        location_mult = 1.5 if store.get('coastal', False) else 1.0
        
        # Intensity peaks 2 days before landfall
        days_to_peak = (MILTON_PEAK - date).days
        if days_to_peak >= 0:
            # Ramp up
            time_curve = 1.0 + (2 - days_to_peak) * 0.8
        else:
            # Decay after landfall
            time_curve = max(0.5, 1.0 + days_to_peak * 0.4)
        
        # Product relevance
        hurricane_mult = product['hurricane_multiplier']
        
        total_mult = location_mult * time_curve * hurricane_mult
        
        # Cap extreme values
        return min(5.0, max(0.5, total_mult))


def main():
    """Generate and save sales data."""
    # Load prerequisite data
    stores_df = pd.read_csv('data/output/stores.csv')
    products_df = pd.read_csv('data/output/products.csv')
    
    generator = SalesGenerator(stores_df, products_df)
    sales_df = generator.generate()
    
    output_path = 'data/output/sales_history.csv'
    sales_df.to_csv(output_path, index=False)
    
    print('\nSaved {} records -> {}'.format(len(sales_df), output_path))
    print('\nSales summary:')
    print('Total revenue: ${:,.0f}'.format(sales_df['revenue'].sum()))
    print('Date range: {} to {}'.format(sales_df['date'].min(), sales_df['date'].max()))
    print('Unique stores: {}'.format(sales_df['store_id'].nunique()))
    print('Unique SKUs: {}'.format(sales_df['sku'].nunique()))
    
    # Hurricane Milton impact analysis
    milton_sales = sales_df[
        (sales_df['date'] >= '2024-10-07') & 
        (sales_df['date'] <= '2024-10-12')
    ]
    normal_sales = sales_df[
        (sales_df['date'] >= '2024-09-07') & 
        (sales_df['date'] <= '2024-09-12')
    ]
    
    print('\nHurricane Milton impact:')
    print('Milton period revenue: ${:,.0f}'.format(milton_sales['revenue'].sum()))
    print('Normal period revenue: ${:,.0f}'.format(normal_sales['revenue'].sum()))
    pct_increase = ((milton_sales['revenue'].sum() / normal_sales['revenue'].sum()) - 1) * 100
    print('Revenue increase: {:.1f}%'.format(pct_increase))


if __name__ == '__main__':
    main()
