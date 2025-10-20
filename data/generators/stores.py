"""Store data generator for StormGuard.

Generates realistic retail store locations across Florida with varying
characteristics like size, traffic, and operational capacity.
"""

import pandas as pd
import numpy as np
from datetime import datetime


# Florida cities with realistic coordinates
FLORIDA_CITIES = [
    ('Miami', 25.7617, -80.1918, 'high'),
    ('Tampa', 27.9506, -82.4572, 'high'),
    ('Orlando', 28.5383, -81.3792, 'high'),
    ('Jacksonville', 30.3322, -81.6557, 'high'),
    ('Fort Lauderdale', 26.1224, -80.1373, 'high'),
    ('West Palm Beach', 26.7153, -80.0534, 'medium'),
    ('Tallahassee', 30.4383, -84.2807, 'medium'),
    ('Pensacola', 30.4213, -87.2169, 'medium'),
    ('Cape Coral', 26.5629, -81.9495, 'medium'),
    ('Port St. Lucie', 27.2730, -80.3582, 'medium'),
    ('Gainesville', 29.6516, -82.3248, 'low'),
    ('Lakeland', 28.0395, -81.9498, 'low'),
    ('Sarasota', 27.3364, -82.5307, 'medium'),
    ('Clearwater', 27.9659, -82.8001, 'medium'),
    ('Naples', 26.1420, -81.7948, 'low'),
    ('Daytona Beach', 29.2108, -81.0228, 'medium'),
    ('Boca Raton', 26.3683, -80.1289, 'medium'),
    ('Ocala', 29.1872, -82.1401, 'low'),
    ('Palm Bay', 28.0345, -80.5887, 'low'),
    ('St. Petersburg', 27.7676, -82.6403, 'high'),
]


class StoreGenerator(object):
    """Generates synthetic but realistic store data for Florida retail chain."""
    
    def __init__(self, num_stores=50, seed=42):
        """Initialize generator.
        
        Args:
            num_stores: Number of stores to generate
            seed: Random seed for reproducibility
        """
        self.num_stores = num_stores
        self.seed = seed
        np.random.seed(seed)
        
    def generate(self):
        """Generate complete store dataset.
        
        Returns:
            pandas.DataFrame with store attributes
        """
        stores = []
        
        # Some cities get multiple stores based on density
        city_weights = self._get_city_weights()
        selected_cities = np.random.choice(
            len(FLORIDA_CITIES),
            size=self.num_stores,
            p=city_weights,
            replace=True
        )
        
        for i in range(self.num_stores):
            city_idx = selected_cities[i]
            city_name, base_lat, base_lon, density = FLORIDA_CITIES[city_idx]
            
            # Add small random offset for multiple stores in same city
            lat = base_lat + np.random.uniform(-0.1, 0.1)
            lon = base_lon + np.random.uniform(-0.1, 0.1)
            
            store = self._generate_single_store(
                store_id=i + 1,
                city=city_name,
                lat=lat,
                lon=lon,
                density=density
            )
            stores.append(store)
        
        df = pd.DataFrame(stores)
        
        # Ensure some stores are in hurricane-prone coastal areas
        df['coastal'] = df['city'].isin([
            'Miami', 'Tampa', 'Fort Lauderdale', 
            'Naples', 'Daytona Beach'
        ])
        
        return df
    
    def _generate_single_store(self, store_id, city, lat, lon, density):
        """Generate attributes for a single store.
        
        Args:
            store_id: Unique store identifier
            city: City name
            lat: Latitude
            lon: Longitude
            density: Population density tier
            
        Returns:
            dict with store attributes
        """
        # Square footage varies by density
        sqft_ranges = {
            'high': (15000, 45000),
            'medium': (10000, 30000),
            'low': (5000, 20000)
        }
        min_sqft, max_sqft = sqft_ranges[density]
        square_footage = np.random.randint(min_sqft, max_sqft)
        
        # Daily traffic correlates with store size
        traffic_per_sqft = np.random.uniform(0.08, 0.15)
        daily_traffic = int(square_footage * traffic_per_sqft)
        
        # Operational characteristics
        store = {
            'store_id': store_id,
            'store_name': 'StormGuard #{:03d}'.format(store_id),
            'city': city,
            'latitude': round(lat, 6),
            'longitude': round(lon, 6),
            'square_footage': square_footage,
            'daily_traffic': daily_traffic,
            'staff_count': max(5, int(square_footage / 2000)),
            'parking_spaces': int(square_footage / 100),
            'warehouse_capacity_pallets': int(square_footage / 50),
            'opened_date': self._random_opening_date(),
            'store_format': self._assign_format(square_footage),
            'population_density': density
        }
        
        return store
    
    def _get_city_weights(self):
        """Calculate probability weights for city selection.
        
        High-density cities get more stores.
        
        Returns:
            numpy array of probabilities
        """
        weights = []
        for _, _, _, density in FLORIDA_CITIES:
            if density == 'high':
                weights.append(0.15)
            elif density == 'medium':
                weights.append(0.08)
            else:
                weights.append(0.03)
        
        weights = np.array(weights)
        return weights / weights.sum()
    
    def _random_opening_date(self):
        """Generate random store opening date between 2015-2022.
        
        Returns:
            datetime string
        """
        start = datetime(2015, 1, 1)
        end = datetime(2022, 12, 31)
        delta = end - start
        random_days = np.random.randint(0, delta.days)
        opening = start + pd.Timedelta(days=int(random_days))
        return opening.strftime('%Y-%m-%d')
    
    def _assign_format(self, square_footage):
        """Assign store format based on size.
        
        Args:
            square_footage: Store size in sqft
            
        Returns:
            str store format
        """
        if square_footage > 30000:
            return 'Superstore'
        elif square_footage > 15000:
            return 'Standard'
        else:
            return 'Express'


def main():
    """Generate and save store data."""
    generator = StoreGenerator(num_stores=50)
    stores_df = generator.generate()
    
    output_path = 'data/output/stores.csv'
    stores_df.to_csv(output_path, index=False)
    print('Generated {} stores -> {}'.format(len(stores_df), output_path))
    print('\nStore format distribution:')
    print(stores_df['store_format'].value_counts())
    print('\nDensity distribution:')
    print(stores_df['population_density'].value_counts())


if __name__ == '__main__':
    main()
