"""News and events data fetcher for StormGuard.

Integrates with NewsAPI to detect demand-impacting events like:
- Hurricane warnings
- Major sports events (Super Bowl, playoffs)
- Festivals and concerts
- Supply chain disruptions
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os


# Pre-defined high-impact events for demo
KNOWN_EVENTS = {
    '2024-02-11': {
        'event': 'Super Bowl LVIII',
        'location': 'Las Vegas',
        'impact_categories': ['Snacks', 'Beverages'],
        'demand_multiplier': 2.5,
        'lead_time_days': 7
    },
    '2024-07-04': {
        'event': 'Independence Day',
        'location': 'Nationwide',
        'impact_categories': ['Snacks', 'Beverages', 'Meat'],
        'demand_multiplier': 1.8,
        'lead_time_days': 3
    },
    '2024-10-07': {
        'event': 'Hurricane Milton Warning',
        'location': 'Florida',
        'impact_categories': ['Water', 'Batteries', 'Flashlights', 'Canned Goods'],
        'demand_multiplier': 3.5,
        'lead_time_days': 2
    },
    '2024-11-28': {
        'event': 'Thanksgiving',
        'location': 'Nationwide',
        'impact_categories': ['Turkey', 'Frozen Foods', 'Canned Goods'],
        'demand_multiplier': 2.2,
        'lead_time_days': 7
    }
}


class NewsAPI(object):
    """Wrapper for NewsAPI event detection."""
    
    def __init__(self, api_key=None):
        """Initialize news API client.
        
        Args:
            api_key: NewsAPI key (or set NEWS_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('NEWS_API_KEY')
        self.base_url = 'https://newsapi.org/v2'
        
    def search_events(self, query, from_date=None, to_date=None):
        """Search for news articles about events.
        
        Args:
            query: Search query string
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            
        Returns:
            list of article dicts
        """
        if not self.api_key:
            return self._mock_search_results(query)
        
        endpoint = '{}/everything'.format(self.base_url)
        
        params = {
            'q': query,
            'apiKey': self.api_key,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': 20
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('articles', [])
        except Exception as e:
            print('News API error: {}'.format(e))
            return self._mock_search_results(query)
    
    def detect_hurricane_warnings(self, region='Florida'):
        """Search for recent hurricane warnings in region.
        
        Args:
            region: Geographic region name
            
        Returns:
            list of hurricane-related articles
        """
        query = 'hurricane warning {}'.format(region)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        return self.search_events(query, from_date=yesterday)
    
    def detect_sports_events(self):
        """Search for major sports events.
        
        Returns:
            list of sports-related articles
        """
        query = 'super bowl OR playoff OR championship'
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        return self.search_events(query, from_date=week_ago)
    
    def detect_supply_disruptions(self):
        """Search for supply chain disruption news.
        
        Returns:
            list of supply chain articles
        """
        query = 'supply chain disruption OR shortage OR recall'
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        return self.search_events(query, from_date=week_ago)
    
    def get_known_event(self, date_str):
        """Get known high-impact event for date.
        
        Args:
            date_str: Date string (YYYY-MM-DD)
            
        Returns:
            dict with event data or None
        """
        return KNOWN_EVENTS.get(date_str)
    
    def get_upcoming_events(self, days_ahead=14):
        """Get all known events in next N days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            list of event dicts
        """
        today = datetime.now()
        cutoff = today + timedelta(days=days_ahead)
        
        upcoming = []
        for date_str, event_data in KNOWN_EVENTS.items():
            event_date = datetime.strptime(date_str, '%Y-%m-%d')
            if today <= event_date <= cutoff:
                upcoming.append({
                    'date': date_str,
                    **event_data
                })
        
        return sorted(upcoming, key=lambda x: x['date'])
    
    def classify_event_impact(self, article_text):
        """Classify potential demand impact from article text.
        
        Args:
            article_text: Article content string
            
        Returns:
            dict with impact classification
        """
        text_lower = article_text.lower()
        
        impact = {
            'severity': 'low',
            'categories_affected': [],
            'estimated_multiplier': 1.0
        }
        
        # Hurricane detection
        if 'hurricane' in text_lower or 'tropical storm' in text_lower:
            impact['severity'] = 'high'
            impact['categories_affected'] = ['Water', 'Batteries', 'Flashlights', 'Canned Goods']
            impact['estimated_multiplier'] = 3.0
        
        # Major sports event
        elif 'super bowl' in text_lower or 'championship' in text_lower:
            impact['severity'] = 'medium'
            impact['categories_affected'] = ['Snacks', 'Beverages']
            impact['estimated_multiplier'] = 2.0
        
        # Supply disruption
        elif 'shortage' in text_lower or 'supply chain' in text_lower:
            impact['severity'] = 'medium'
            impact['categories_affected'] = ['Various']
            impact['estimated_multiplier'] = 1.5
        
        return impact
    
    def _mock_search_results(self, query):
        """Generate mock search results (for testing without API key).
        
        Args:
            query: Search query
            
        Returns:
            list of mock articles
        """
        mock_articles = [
            {
                'title': 'Hurricane Milton Strengthens to Category 4',
                'description': 'Hurricane Milton has rapidly intensified to Category 4 with winds of 145 mph, threatening Florida\'s west coast.',
                'url': 'https://example.com/milton-cat4',
                'publishedAt': '2024-10-08T14:30:00Z',
                'source': {'name': 'Weather Channel'}
            },
            {
                'title': 'Florida Prepares for Major Hurricane Impact',
                'description': 'Residents stocking up on supplies as Hurricane Milton approaches. Stores report shortages of water and batteries.',
                'url': 'https://example.com/florida-prepares',
                'publishedAt': '2024-10-08T16:45:00Z',
                'source': {'name': 'CNN'}
            }
        ]
        return mock_articles


def main():
    """Test news API and save known events."""
    api = NewsAPI()
    
    # Test hurricane warning detection
    print('Testing hurricane warning detection...')
    articles = api.detect_hurricane_warnings('Florida')
    print('Found {} articles about hurricanes'.format(len(articles)))
    if articles:
        print('Sample: {}'.format(articles[0]['title']))
    
    # Test event impact classification
    print('\nTesting event classification...')
    sample_text = 'Hurricane Milton threatens Florida with 145 mph winds'
    impact = api.classify_event_impact(sample_text)
    print('Severity: {}'.format(impact['severity']))
    print('Affected categories: {}'.format(impact['categories_affected']))
    
    # Get upcoming events
    print('\nGetting upcoming events...')
    upcoming = api.get_upcoming_events(days_ahead=30)
    print('Found {} upcoming events:'.format(len(upcoming)))
    for event in upcoming:
        print('  {} - {}'.format(event['date'], event['event']))
    
    # Save known events
    print('\nSaving known events data...')
    events_df = pd.DataFrame([
        {'date': date, **data}
        for date, data in KNOWN_EVENTS.items()
    ])
    
    output_path = 'data/output/known_events.csv'
    events_df.to_csv(output_path, index=False)
    print('Saved events -> {}'.format(output_path))


if __name__ == '__main__':
    main()
