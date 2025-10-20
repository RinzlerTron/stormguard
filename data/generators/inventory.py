"""Inventory state generator for StormGuard.

Generates current inventory levels, reorder points, and on-order quantities
for all store-SKU combinations.
"""

import pandas as pd
import numpy as np


class InventoryGenerator(object):
    """Generates current inventory snapshot for all stores."""
    
    def __init__(self, stores_df, products_df, sales_df, seed=42):
        """Initialize inventory generator.
        
        Args:
            stores_df: DataFrame of stores
            products_df: DataFrame of products  
            sales_df: Historical sales DataFrame
            seed: Random seed
        """
        self.stores = stores_df
        self.products = products_df
        self.sales = sales_df
        self.seed = seed
        np.random.seed(seed)
        
    def generate(self):
        """Generate current inventory state.
        
        Returns:
            pandas.DataFrame with inventory by store-SKU
        """
        print('Generating inventory for {} stores x {} SKUs...'.format(
            len(self.stores), len(self.products)))
        
        # Calculate average daily velocity per store-SKU from recent sales
        velocities = self._calculate_velocities()
        
        inventory_records = []
        
        for _, store in self.stores.iterrows():
            for _, product in self.products.iterrows():
                inv_record = self._generate_inventory_record(
                    store, product, velocities
                )
                inventory_records.append(inv_record)
        
        df = pd.DataFrame(inventory_records)
        
        print('Generated {} inventory records'.format(len(df)))
        return df
    
    def _generate_inventory_record(self, store, product, velocities):
        """Generate inventory record for single store-SKU.
        
        Args:
            store: Store Series
            product: Product Series
            velocities: Dict of average daily sales
            
        Returns:
            dict with inventory attributes
        """
        store_id = store['store_id']
        sku = product['sku']
        
        # Get average daily velocity
        velocity_key = (store_id, sku)
        avg_daily_sales = velocities.get(velocity_key, 5.0)
        
        # Lead time from supplier
        lead_time = product['supplier_lead_time_days']
        
        # Safety stock calculation (covers lead time + buffer)
        # Rule: hold enough for lead_time * 1.5 at average velocity
        safety_stock = int(avg_daily_sales * lead_time * 1.5)
        safety_stock = max(10, safety_stock)
        
        # Reorder point (when to trigger new order)
        # Rule: safety stock + expected demand during lead time
        reorder_point = int(safety_stock + avg_daily_sales * lead_time)
        
        # Current on-hand inventory
        # Randomize between 0.5x and 2.5x reorder point
        on_hand = int(reorder_point * np.random.uniform(0.5, 2.5))
        on_hand = max(0, on_hand)
        
        # On-order quantity (if already below reorder point)
        on_order = 0
        if on_hand < reorder_point:
            # Order to bring up to target level (2x reorder point)
            target_level = reorder_point * 2
            order_qty = target_level - on_hand
            # Round to MOQ
            moq = product['min_order_qty']
            on_order = int(np.ceil(order_qty / moq) * moq)
        
        # Calculate days of supply
        days_of_supply = on_hand / avg_daily_sales if avg_daily_sales > 0 else 999
        
        # Stockout risk score (0-100)
        if on_hand == 0:
            stockout_risk = 100
        elif on_hand < safety_stock:
            stockout_risk = 80
        elif on_hand < reorder_point:
            stockout_risk = 50
        else:
            stockout_risk = 10
        
        record = {
            'store_id': store_id,
            'sku': sku,
            'on_hand_qty': on_hand,
            'on_order_qty': on_order,
            'safety_stock': safety_stock,
            'reorder_point': reorder_point,
            'max_capacity': int(reorder_point * 3),
            'avg_daily_sales': round(avg_daily_sales, 2),
            'days_of_supply': round(days_of_supply, 1),
            'stockout_risk_score': stockout_risk,
            'last_received_date': self._random_recent_date(),
            'expected_delivery_date': self._expected_delivery(on_order > 0, lead_time)
        }
        
        return record
    
    def _calculate_velocities(self):
        """Calculate average daily velocity per store-SKU from recent sales.
        
        Uses last 30 days of sales data.
        
        Returns:
            dict mapping (store_id, sku) to avg daily quantity
        """
        print('Calculating velocities from sales history...')
        
        # Get last 30 days
        self.sales['date'] = pd.to_datetime(self.sales['date'])
        max_date = self.sales['date'].max()
        cutoff_date = max_date - pd.Timedelta(days=30)
        recent_sales = self.sales[self.sales['date'] >= cutoff_date]
        
        # Group by store and SKU
        velocity_df = recent_sales.groupby(['store_id', 'sku']).agg({
            'quantity_sold': 'sum'
        }).reset_index()
        
        velocity_df['avg_daily'] = velocity_df['quantity_sold'] / 30.0
        
        # Convert to dict
        velocities = {}
        for _, row in velocity_df.iterrows():
            key = (row['store_id'], row['sku'])
            velocities[key] = row['avg_daily']
        
        print('Calculated velocities for {} store-SKU pairs'.format(len(velocities)))
        return velocities
    
    def _random_recent_date(self):
        """Generate random date within last 14 days.
        
        Returns:
            str date
        """
        days_ago = np.random.randint(0, 14)
        date = pd.Timestamp.now() - pd.Timedelta(days=days_ago)
        return date.strftime('%Y-%m-%d')
    
    def _expected_delivery(self, has_order, lead_time):
        """Generate expected delivery date for on-order inventory.
        
        Args:
            has_order: bool whether there's an outstanding order
            lead_time: int supplier lead time days
            
        Returns:
            str date or None
        """
        if not has_order:
            return None
        
        # Random days until delivery (within lead time window)
        days_until = np.random.randint(1, lead_time + 1)
        delivery = pd.Timestamp.now() + pd.Timedelta(days=days_until)
        return delivery.strftime('%Y-%m-%d')


def main():
    """Generate and save inventory data."""
    # Load prerequisite data
    stores_df = pd.read_csv('data/output/stores.csv')
    products_df = pd.read_csv('data/output/products.csv')
    sales_df = pd.read_csv('data/output/sales_history.csv')
    
    generator = InventoryGenerator(stores_df, products_df, sales_df)
    inventory_df = generator.generate()
    
    output_path = 'data/output/inventory.csv'
    inventory_df.to_csv(output_path, index=False)
    
    print('\nSaved {} records -> {}'.format(len(inventory_df), output_path))
    print('\nInventory summary:')
    print('Total units on hand: {:,.0f}'.format(inventory_df['on_hand_qty'].sum()))
    print('Total units on order: {:,.0f}'.format(inventory_df['on_order_qty'].sum()))
    print('High stockout risk (score >= 80): {}'.format(
        len(inventory_df[inventory_df['stockout_risk_score'] >= 80])
    ))
    print('Average days of supply: {:.1f}'.format(inventory_df['days_of_supply'].mean()))


if __name__ == '__main__':
    main()
