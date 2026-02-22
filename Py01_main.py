import requests
import json
from typing import List, Dict, Optional
from datetime import datetime

class PolymarketSportsAPI:
    def __init__(self):
        self.base_url = "https://gamma-api.polymarket.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; PolymarketBot/1.0)',
            'Accept': 'application/json'})
    def fetch_all_markets(self, limit: int = 100, offset: int = 0) -> Dict:
        url = f"{self.base_url}/markets"
        params = {
            'limit': limit,
            'offset': offset,
            'closed': 'false',  # Only active markets
            'order': 'volume24hr',
            'ascending': 'false'}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching markets: {e}")
            return {}
    
    def is_sports_market(self, market: Dict) -> bool:
        sports_keywords = ['football', 'soccer', 'basketball', 'baseball', 'tennis','hockey', 'golf', 'boxing', 'mma', 'nfl', 'nba', 'mlb','nhl', 'uefa', 'fifa', 'olympics', 'playoff', 'championship','super bowl', 'world cup', 'premier league', 'champions league','sports', 'game', 'match', 'tournament', 'season', 'draft']
        
        title = market.get('question', '').lower()
        description = market.get('description', '').lower()
        tags = [tag.lower() for tag in market.get('tags', [])]
        
        # Check title, description, and tags
        text_to_check = f"{title} {description} {' '.join(tags)}"
        
        return any(keyword in text_to_check for keyword in sports_keywords)
    
    def fetch_sports_events(self, max_results: int = 500) -> List[Dict]:
        sports_events = []
        offset = 0
        limit = 100
        
        print("Fetching Polymarket sports events...")
        
        while len(sports_events) < max_results:
            print(f"Fetching batch {offset//limit + 1}...")
            
            data = self.fetch_all_markets(limit=limit, offset=offset)
            markets = data.get('data', [])
            
            if not markets:
                break
            
            # Filter for sports events
            for market in markets:
                if self.is_sports_market(market):
                    sports_events.append(self.format_event(market))
            
            offset += limit
            
            # Break if we got fewer results than requested (end of data)
            if len(markets) < limit:
                break
        
        return sports_events[:max_results]
    
    def format_event(self, market: Dict) -> Dict:
        return {
            'id': market.get('id'),
            'question': market.get('question'),
            'description': market.get('description'),
            'end_date': market.get('endDate'),
            'end_date_iso': market.get('endDateIso'),
            'volume': market.get('volume'),
            'volume_24hr': market.get('volume24hr'),
            'liquidity': market.get('liquidity'),
            'outcomes': [
                {
                    'name': outcome.get('name'),
                    'price': outcome.get('price'),
                    'percentage': f"{float(outcome.get('price', 0)) * 100:.1f}%"
                }
                for outcome in market.get('outcomes', [])
            ],
            'tags': market.get('tags', []),
            'image': market.get('image'),
            'url': f"https://polymarket.com/event/{market.get('slug', '')}"
        }
    
    def save_to_json(self, events: List[Dict], filename: str = 'polymarket_sports.json'):
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_events': len(events),
                'events': events
            }, f, indent=2)
        print(f"Saved {len(events)} events to {filename}")
# Usage example
if __name__ == "__main__":
    api = PolymarketSportsAPI()
    
    # Fetch sports events
    sports_events = api.fetch_sports_events(max_results=200)
    
    # Display results
    print(f"\nFound {len(sports_events)} sports events:")
    print("-" * 50)
    
    for i, event in enumerate(sports_events[:10], 1):  # Show first 10
        print(f"{i}. {event['question']}")
        print(f"   End Date: {event['end_date']}")
        print(f"   Volume (24h): ${event['volume_24hr']:,.2f}" if event['volume_24hr'] else "   Volume (24h): N/A")
        print(f"   Outcomes: {', '.join([f\"{o['name']}: {o['percentage']}\" for o in event['outcomes']])}")
        print()
    
    # Save to file
    api.save_to_json(sports_events)
    
    # Summary statistics
    total_volume = sum(float(event['volume_24hr'] or 0) for event in sports_events)
    print(f"\nSummary:")
    print(f"Total sports events found: {len(sports_events)}")
    print(f"Total 24h volume: ${total_volume:,.2f}")
