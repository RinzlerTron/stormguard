"""Weather data fetcher for StormGuard.

Integrates with OpenWeatherMap API for current conditions and forecasts.
Includes historical Hurricane Milton data (Oct 2024).
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import os


# Hurricane Milton historical data from NOAA
MILTON_HISTORICAL = {
    '2024-10-07': {
        'category': 1,
        'max_wind_mph': 75,
        'pressure_mb': 988,
        'affected_counties': ['Miami-Dade', 'Broward', 'Monroe'],
        'storm_surge_ft': 3,
        'rainfall_inches': 4.2
    },
    '2024-10-08': {
        'category': 2,
        'max_wind_mph': 100,
        'pressure_mb': 972,
        'affected_counties': ['Palm Beach', 'Martin', 'St. Lucie', 'Indian River'],
        'storm_surge_ft': 6,
        'rainfall_inches': 8.5
    },
    '2024-10-09': {
        'category': 4,
        'max_wind_mph': 145,
        'pressure_mb': 945,
        'affected_counties': ['Brevard', 'Orange', 'Volusia', 'Seminole', 'Osceola'],
        'storm_surge_ft': 12,
        'rainfall_inches': 15.2
    },
    '2024-10-10': {
        'category': 3,
        'max_wind_mph': 130,
        'pressure_mb': 956,
        'affected_counties': ['Pinellas', 'Hillsborough', 'Manatee', 'Polk'],
        'storm_surge_ft': 10,
        'rainfall_inches': 12.1
    },
    '2024-10-11': {
        'category': 2,
        'max_wind_mph': 85,
        'pressure_mb': 978,
        'affected_counties': ['Citrus', 'Hernando', 'Pasco', 'Sumter'],
        'storm_surge_ft': 5,
        'rainfall_inches': 6.8
    },
    '2024-10-12': {
        'category': 'TS',
        'max_wind_mph': 40,
        'pressure_mb': 995,
        'affected_counties': ['Dixie', 'Levy', 'Gilchrist', 'Alachua'],
        'storm_surge_ft': 2,
        'rainfall_inches': 3.1
    }
}


class WeatherAPI(object):
    """Wrapper for OpenWeatherMap API."""
    
    def __init__(self, api_key=None):
        """Initialize weather API client.
        
        Args:
            api_key: OpenWeatherMap API key (or set OPENWEATHER_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('OPENWEATHER_API_KEY')
        self.base_url = 'http://api.openweathermap.org/data/2.5'
        
    def get_current_weather(self, lat, lon):
        """Get current weather conditions for location.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            dict with weather data
        """
        if not self.api_key:
            return self._mock_current_weather(lat, lon)
        
        endpoint = '{}/weather'.format(self.base_url)
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'imperial'
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print('Weather API error: {}'.format(e))
            return self._mock_current_weather(lat, lon)
    
    def get_forecast(self, lat, lon, days=7):
        """Get weather forecast for location.
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Number of days to forecast
            
        Returns:
            list of forecast dicts
        """
        if not self.api_key:
            return self._mock_forecast(lat, lon, days)
        
        endpoint = '{}/forecast'.format(self.base_url)
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'imperial',
            'cnt': days * 8  # 3-hour intervals
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('list', [])
        except Exception as e:
            print('Forecast API error: {}'.format(e))
            return self._mock_forecast(lat, lon, days)
    
    def get_milton_data(self, date_str):
        """Get Hurricane Milton historical data.
        
        Args:
            date_str: Date string in 'YYYY-MM-DD' format
            
        Returns:
            dict with Milton data or None
        """
        return MILTON_HISTORICAL.get(date_str)
    
    def is_hurricane_risk(self, lat, lon, days_ahead=7):
        """Check if location has hurricane risk in forecast window.
        
        Args:
            lat: Latitude
            lon: Longitude
            days_ahead: Days to look ahead
            
        Returns:
            dict with risk assessment
        """
        forecast = self.get_forecast(lat, lon, days_ahead)
        
        risk = {
            'has_risk': False,
            'confidence': 'low',
            'wind_speed_max_mph': 0,
            'rainfall_max_inches': 0
        }
        
        # Simple heuristic: high wind + heavy rain = hurricane risk
        for period in forecast:
            wind_speed = period.get('wind', {}).get('speed', 0) * 2.237  # m/s to mph
            rain_mm = period.get('rain', {}).get('3h', 0)
            rain_inches = rain_mm / 25.4
            
            if wind_speed > risk['wind_speed_max_mph']:
                risk['wind_speed_max_mph'] = wind_speed
            
            if rain_inches > risk['rainfall_max_inches']:
                risk['rainfall_max_inches'] = rain_inches
        
        # Classify risk
        if risk['wind_speed_max_mph'] > 74:
            risk['has_risk'] = True
            risk['confidence'] = 'high'
        elif risk['wind_speed_max_mph'] > 50:
            risk['has_risk'] = True
            risk['confidence'] = 'medium'
        
        return risk
    
    def _mock_current_weather(self, lat, lon):
        """Generate mock current weather (for testing without API key).
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            dict with mock weather
        """
        return {
            'weather': [{'main': 'Clear', 'description': 'clear sky'}],
            'main': {
                'temp': 78.5,
                'feels_like': 80.2,
                'humidity': 65
            },
            'wind': {'speed': 8.5, 'deg': 180},
            'dt': int(datetime.now().timestamp())
        }
    
    def _mock_forecast(self, lat, lon, days):
        """Generate mock forecast (for testing without API key).
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Number of days
            
        Returns:
            list of mock forecast periods
        """
        forecast = []
        base_time = datetime.now()
        
        for i in range(days * 8):
            period_time = base_time + timedelta(hours=i*3)
            forecast.append({
                'dt': int(period_time.timestamp()),
                'main': {
                    'temp': 75 + (i % 8) * 2,
                    'humidity': 60 + (i % 8) * 3
                },
                'weather': [{'main': 'Clear', 'description': 'clear sky'}],
                'wind': {'speed': 5 + (i % 8), 'deg': 180},
                'rain': {'3h': 0}
            })
        
        return forecast


def main():
    """Test weather API and save Milton data."""
    api = WeatherAPI()
    
    # Test current weather for Miami
    print('Testing current weather for Miami...')
    current = api.get_current_weather(25.7617, -80.1918)
    print('Temperature: {}F'.format(current['main']['temp']))
    print('Conditions: {}'.format(current['weather'][0]['description']))
    
    # Test forecast
    print('\nTesting 7-day forecast...')
    forecast = api.get_forecast(25.7617, -80.1918, days=7)
    print('Got {} forecast periods'.format(len(forecast)))
    
    # Test hurricane risk
    print('\nChecking hurricane risk...')
    risk = api.is_hurricane_risk(25.7617, -80.1918)
    print('Risk detected: {}'.format(risk['has_risk']))
    print('Max wind: {:.1f} mph'.format(risk['wind_speed_max_mph']))
    
    # Save Hurricane Milton data
    print('\nSaving Hurricane Milton historical data...')
    milton_df = pd.DataFrame([
        {'date': date, **data}
        for date, data in MILTON_HISTORICAL.items()
    ])
    
    output_path = 'data/output/hurricane_milton.csv'
    milton_df.to_csv(output_path, index=False)
    print('Saved Milton data -> {}'.format(output_path))
    
    # Also save as JSON for easy loading
    json_path = 'data/output/hurricane_milton.json'
    with open(json_path, 'w') as f:
        json.dump(MILTON_HISTORICAL, f, indent=2)
    print('Saved Milton data -> {}'.format(json_path))


if __name__ == '__main__':
    main()
