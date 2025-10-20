"""Forecast tool for StormGuard demand intelligence.

Provides demand forecasting capabilities using:
- Historical sales patterns
- Seasonal trends
- External signals (weather, events)
- Prophet time series model
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class ForecastTool(object):
    """Tool for generating demand forecasts."""
    
    def __init__(self, sales_df, products_df, stores_df):
        """Initialize forecast tool.
        
        Args:
            sales_df: Historical sales DataFrame
            products_df: Products DataFrame
            stores_df: Stores DataFrame
        """
        self.sales = sales_df
        self.products = products_df
        self.stores = stores_df
        
        # Ensure date column is datetime
        if 'date' in self.sales.columns:
            self.sales['date'] = pd.to_datetime(self.sales['date'])
    
    def query(self, sku, store_id=None, horizon_days=7, include_confidence=True):
        """Generate demand forecast for SKU.
        
        Args:
            sku: Product SKU to forecast
            store_id: Specific store (None = all stores aggregate)
            horizon_days: Number of days to forecast ahead
            include_confidence: Include confidence intervals
            
        Returns:
            dict with forecast data
        """
        # Filter historical data
        hist_data = self.sales[self.sales['sku'] == sku].copy()
        
        if store_id:
            hist_data = hist_data[hist_data['store_id'] == store_id]
        
        if len(hist_data) < 30:
            # Not enough history - return baseline
            return self._baseline_forecast(sku, store_id, horizon_days)
        
        # Aggregate by date
        daily_sales = hist_data.groupby('date').agg({
            'quantity_sold': 'sum'
        }).reset_index()
        
        # Use simple moving average + trend for now
        # In production, use Prophet or similar
        forecast = self._simple_forecast(
            daily_sales,
            horizon_days,
            include_confidence
        )
        
        # Get product metadata
        product = self.products[self.products['sku'] == sku].iloc[0]
        
        result = {
            'sku': sku,
            'store_id': store_id,
            'forecast_date': datetime.now().strftime('%Y-%m-%d'),
            'horizon_days': horizon_days,
            'forecast': forecast,
            'baseline_daily_qty': forecast['mean'][0] if forecast['mean'] else 0,
            'total_forecast_qty': sum(forecast['mean']),
            'product_category': product['category'],
            'hurricane_multiplier': product['hurricane_multiplier']
        }
        
        return result
    
    def bulk_forecast(self, sku_list, store_id=None, horizon_days=7):
        """Generate forecasts for multiple SKUs.
        
        Args:
            sku_list: List of SKU strings
            store_id: Optional store filter
            horizon_days: Forecast horizon
            
        Returns:
            list of forecast dicts
        """
        forecasts = []
        for sku in sku_list:
            forecast = self.query(sku, store_id, horizon_days, include_confidence=False)
            forecasts.append(forecast)
        return forecasts
    
    def adjust_for_event(self, base_forecast, event_type, event_date, sku):
        """Adjust forecast for known event impact.
        
        Args:
            base_forecast: Base forecast dict
            event_type: Event type (hurricane, sports, holiday)
            event_date: Date string of event
            sku: Product SKU
            
        Returns:
            dict with adjusted forecast
        """
        product = self.products[self.products['sku'] == sku].iloc[0]
        
        # Get event multiplier based on product category
        multipliers = {
            'hurricane': product.get('hurricane_multiplier', 1.0),
            'sports': 1.5 if product['category'] in ['Snacks', 'Beverages'] else 1.0,
            'holiday': 1.3
        }
        
        event_mult = multipliers.get(event_type, 1.0)
        
        # Apply multiplier with decay before/after event
        adjusted_forecast = base_forecast.copy()
        event_dt = pd.to_datetime(event_date)
        
        for i, date_str in enumerate(base_forecast['dates']):
            date_dt = pd.to_datetime(date_str)
            days_to_event = (event_dt - date_dt).days
            
            # Peak at event, decay before and after
            if abs(days_to_event) <= 3:
                decay = 1.0 - (abs(days_to_event) / 4.0)
                mult = 1.0 + (event_mult - 1.0) * decay
                adjusted_forecast['mean'][i] *= mult
                if 'lower' in adjusted_forecast:
                    adjusted_forecast['lower'][i] *= mult
                if 'upper' in adjusted_forecast:
                    adjusted_forecast['upper'][i] *= mult
        
        return adjusted_forecast
    
    def _simple_forecast(self, daily_sales, horizon_days, include_confidence):
        """Generate simple forecast using moving average.
        
        Args:
            daily_sales: DataFrame with date and quantity_sold
            horizon_days: Days to forecast
            include_confidence: Include confidence bands
            
        Returns:
            dict with forecast arrays
        """
        # Calculate 7-day and 30-day moving averages
        recent_7 = daily_sales.tail(7)['quantity_sold'].mean()
        recent_30 = daily_sales.tail(30)['quantity_sold'].mean()
        
        # Weight recent data more heavily
        base_qty = recent_7 * 0.7 + recent_30 * 0.3
        
        # Detect trend
        first_half = daily_sales.head(len(daily_sales) // 2)['quantity_sold'].mean()
        second_half = daily_sales.tail(len(daily_sales) // 2)['quantity_sold'].mean()
        trend = (second_half - first_half) / first_half if first_half > 0 else 0
        
        # Generate forecast dates
        last_date = daily_sales['date'].max()
        forecast_dates = [
            (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d')
            for i in range(horizon_days)
        ]
        
        # Forecast with trend
        forecast_mean = []
        for i in range(horizon_days):
            trend_adj = 1.0 + (trend * (i + 1) / 30.0)
            qty = base_qty * trend_adj
            forecast_mean.append(max(0, int(qty)))
        
        result = {
            'dates': forecast_dates,
            'mean': forecast_mean
        }
        
        if include_confidence:
            # Simple confidence bands (±20%)
            result['lower'] = [max(0, int(q * 0.8)) for q in forecast_mean]
            result['upper'] = [int(q * 1.2) for q in forecast_mean]
        
        return result
    
    def _baseline_forecast(self, sku, store_id, horizon_days):
        """Generate baseline forecast when insufficient history.
        
        Args:
            sku: Product SKU
            store_id: Store ID or None
            horizon_days: Days to forecast
            
        Returns:
            dict with baseline forecast
        """
        # Use category average or product base
        product = self.products[self.products['sku'] == sku].iloc[0]
        
        # Estimate based on category popularity
        category_baseline = {
            'Water': 15,
            'Batteries': 8,
            'Bread': 20,
            'Milk': 18,
            'Snacks': 25
        }
        
        base_qty = category_baseline.get(product['category'], 10)
        
        forecast_dates = [
            (datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d')
            for i in range(horizon_days)
        ]
        
        return {
            'sku': sku,
            'store_id': store_id,
            'forecast_date': datetime.now().strftime('%Y-%m-%d'),
            'horizon_days': horizon_days,
            'forecast': {
                'dates': forecast_dates,
                'mean': [base_qty] * horizon_days
            },
            'baseline_daily_qty': base_qty,
            'total_forecast_qty': base_qty * horizon_days,
            'product_category': product['category'],
            'note': 'Baseline forecast - insufficient historical data'
        }


def main():
    """Test forecast tool."""
    # Load data
    sales_df = pd.read_csv('data/output/sales_history.csv')
    products_df = pd.read_csv('data/output/products.csv')
    stores_df = pd.read_csv('data/output/stores.csv')
    
    tool = ForecastTool(sales_df, products_df, stores_df)
    
    # Test single forecast
    print('Testing forecast for SKU-0001 (Water)...')
    forecast = tool.query('SKU-0001', horizon_days=7)
    print('Baseline daily qty: {}'.format(forecast['baseline_daily_qty']))
    print('7-day forecast total: {}'.format(forecast['total_forecast_qty']))
    print('Daily forecast: {}'.format(forecast['forecast']['mean']))
    
    # Test event adjustment
    print('\nTesting hurricane adjustment...')
    adjusted = tool.adjust_for_event(
        forecast['forecast'],
        'hurricane',
        '2024-10-09',
        'SKU-0001'
    )
    print('Adjusted forecast: {}'.format(adjusted['mean']))


if __name__ == '__main__':
    main()
