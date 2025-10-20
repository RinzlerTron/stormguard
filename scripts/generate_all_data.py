"""Master data generation script for StormGuard.

Runs all data generators in the correct sequence:
1. Stores
2. Products
3. Sales history (depends on stores + products)
4. Inventory (depends on all above)
5. External data (weather, news)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.generators import stores, products, sales, inventory
from data.external import weather, news


def main():
    """Run complete data generation pipeline."""
    print('=' * 60)
    print('StormGuard Data Generation Pipeline')
    print('=' * 60)
    
    # Step 1: Generate stores
    print('\n[1/6] Generating stores...')
    stores_gen = stores.StoreGenerator(num_stores=50)
    stores_df = stores_gen.generate()
    stores_df.to_csv('data/output/stores.csv', index=False)
    print('  ✓ Generated {} stores'.format(len(stores_df)))
    
    # Step 2: Generate products
    print('\n[2/6] Generating products...')
    products_gen = products.ProductGenerator(num_products=200)
    products_df = products_gen.generate()
    products_df.to_csv('data/output/products.csv', index=False)
    print('  ✓ Generated {} products'.format(len(products_df)))
    
    # Step 3: Generate sales history (this takes a while!)
    print('\n[3/6] Generating sales history (2023-2024)...')
    print('  This may take 2-3 minutes...')
    sales_gen = sales.SalesGenerator(stores_df, products_df)
    sales_df = sales_gen.generate()
    sales_df.to_csv('data/output/sales_history.csv', index=False)
    print('  ✓ Generated {:,} sales records'.format(len(sales_df)))
    
    # Step 4: Generate current inventory
    print('\n[4/6] Generating current inventory...')
    inv_gen = inventory.InventoryGenerator(stores_df, products_df, sales_df)
    inv_df = inv_gen.generate()
    inv_df.to_csv('data/output/inventory.csv', index=False)
    print('  ✓ Generated {} inventory records'.format(len(inv_df)))
    
    # Step 5: Fetch/save external data
    print('\n[5/6] Saving external data...')
    
    # Weather - Hurricane Milton historical
    weather_api = weather.WeatherAPI()
    milton_df = weather_api.get_milton_data('2024-10-09')  # Just get structure
    
    import pandas as pd
    milton_records = []
    for date_str in sorted(weather.MILTON_HISTORICAL.keys()):
        record = {'date': date_str}
        record.update(weather.MILTON_HISTORICAL[date_str])
        milton_records.append(record)
    
    milton_df = pd.DataFrame(milton_records)
    milton_df.to_csv('data/output/hurricane_milton.csv', index=False)
    print('  ✓ Saved Hurricane Milton data')
    
    # News - Known events
    news_api = news.NewsAPI()
    events_records = []
    for date_str in sorted(news.KNOWN_EVENTS.keys()):
        record = {'date': date_str}
        record.update(news.KNOWN_EVENTS[date_str])
        events_records.append(record)
    
    events_df = pd.DataFrame(events_records)
    events_df.to_csv('data/output/known_events.csv', index=False)
    print('  ✓ Saved known events data')
    
    # Step 6: Generate summary statistics
    print('\n[6/6] Generating summary statistics...')
    generate_summary(stores_df, products_df, sales_df, inv_df)
    
    print('\n' + '=' * 60)
    print('✓ Data generation complete!')
    print('=' * 60)
    print('\nOutput files in data/output/:')
    print('  - stores.csv ({} stores)'.format(len(stores_df)))
    print('  - products.csv ({} products)'.format(len(products_df)))
    print('  - sales_history.csv ({:,} records)'.format(len(sales_df)))
    print('  - inventory.csv ({} records)'.format(len(inv_df)))
    print('  - hurricane_milton.csv')
    print('  - known_events.csv')
    print('  - summary_stats.txt')
    print('\nNext steps:')
    print('  1. Review summary_stats.txt')
    print('  2. Run: python scripts/upload_to_s3.py')
    print('  3. Deploy agents: cd infrastructure/terraform && terraform apply')


def generate_summary(stores_df, products_df, sales_df, inv_df):
    """Generate human-readable summary statistics.
    
    Args:
        stores_df: Stores DataFrame
        products_df: Products DataFrame
        sales_df: Sales DataFrame
        inv_df: Inventory DataFrame
    """
    import pandas as pd
    
    summary = []
    summary.append('StormGuard Data Summary')
    summary.append('=' * 60)
    summary.append('')
    
    # Stores
    summary.append('STORES')
    summary.append('-' * 60)
    summary.append('Total stores: {}'.format(len(stores_df)))
    summary.append('Store formats: {}'.format(', '.join(stores_df['store_format'].value_counts().index)))
    summary.append('Total square footage: {:,.0f}'.format(stores_df['square_footage'].sum()))
    summary.append('Avg daily traffic per store: {:,.0f}'.format(stores_df['daily_traffic'].mean()))
    summary.append('')
    
    # Products
    summary.append('PRODUCTS')
    summary.append('-' * 60)
    summary.append('Total SKUs: {}'.format(len(products_df)))
    summary.append('Categories: {}'.format(products_df['category'].nunique()))
    summary.append('Price range: ${:.2f} - ${:.2f}'.format(
        products_df['base_price'].min(), products_df['base_price'].max()
    ))
    summary.append('Avg margin: {:.1f}%'.format(products_df['margin'].mean() * 100))
    summary.append('')
    summary.append('Top hurricane-critical categories:')
    top_hurricane = products_df.nlargest(10, 'hurricane_multiplier')[['category', 'hurricane_multiplier']]
    for _, row in top_hurricane.drop_duplicates('category').head(5).iterrows():
        summary.append('  {} ({}x)'.format(row['category'], row['hurricane_multiplier']))
    summary.append('')
    
    # Sales
    summary.append('SALES HISTORY')
    summary.append('-' * 60)
    summary.append('Date range: {} to {}'.format(sales_df['date'].min(), sales_df['date'].max()))
    summary.append('Total transactions: {:,}'.format(len(sales_df)))
    summary.append('Total revenue: ${:,.0f}'.format(sales_df['revenue'].sum()))
    summary.append('Avg daily revenue: ${:,.0f}'.format(
        sales_df.groupby('date')['revenue'].sum().mean()
    ))
    summary.append('')
    
    # Hurricane Milton impact
    sales_df['date'] = pd.to_datetime(sales_df['date'])
    milton_sales = sales_df[
        (sales_df['date'] >= '2024-10-07') & (sales_df['date'] <= '2024-10-12')
    ]
    baseline_sales = sales_df[
        (sales_df['date'] >= '2024-09-07') & (sales_df['date'] <= '2024-09-12')
    ]
    
    milton_rev = milton_sales['revenue'].sum()
    baseline_rev = baseline_sales['revenue'].sum()
    increase_pct = ((milton_rev / baseline_rev) - 1) * 100
    
    summary.append('Hurricane Milton Impact (Oct 7-12, 2024):')
    summary.append('  Revenue during Milton: ${:,.0f}'.format(milton_rev))
    summary.append('  Baseline revenue: ${:,.0f}'.format(baseline_rev))
    summary.append('  Increase: {:.1f}%'.format(increase_pct))
    summary.append('')
    
    # Inventory
    summary.append('CURRENT INVENTORY')
    summary.append('-' * 60)
    summary.append('Total items on hand: {:,.0f}'.format(inv_df['on_hand_qty'].sum()))
    summary.append('Total items on order: {:,.0f}'.format(inv_df['on_order_qty'].sum()))
    summary.append('Avg days of supply: {:.1f}'.format(inv_df['days_of_supply'].mean()))
    summary.append('')
    
    high_risk = inv_df[inv_df['stockout_risk_score'] >= 80]
    summary.append('Stockout Risk:')
    summary.append('  High risk (score >= 80): {}'.format(len(high_risk)))
    summary.append('  Medium risk (50-79): {}'.format(
        len(inv_df[(inv_df['stockout_risk_score'] >= 50) & (inv_df['stockout_risk_score'] < 80)])
    ))
    summary.append('  Low risk (< 50): {}'.format(
        len(inv_df[inv_df['stockout_risk_score'] < 50])
    ))
    
    # Write to file
    summary_text = '\n'.join(summary)
    with open('data/output/summary_stats.txt', 'w') as f:
        f.write(summary_text)
    
    print(summary_text)


if __name__ == '__main__':
    main()
