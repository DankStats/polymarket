"""Polymarket Gamma API client for sports markets."""

import json
import requests
from datetime import datetime
from typing import Any, Dict, List


class PolymarketSportsAPI:
    """Fetch sports-related markets from Polymarket's Gamma API."""

    def __init__(self):
        self.base_url = "https://gamma-api.polymarket.com"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; PolymarketBot/1.0)",
            "Accept": "application/json",
        })

    def fetch_all_markets(self, limit: int = 100, offset: int = 0) -> Any:
        url = f"{self.base_url}/markets"
        params = {
            "limit": limit,
            "offset": offset,
            "closed": "false",
            "order": "volume24hr",
            "ascending": "false",
        }
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching markets: {e}")
            return []

    @staticmethod
    def _extract_markets(payload: Any) -> List[Dict]:
        """
        Gamma API responses are not fully consistent across endpoints/versions.
        This normalizes either:
        - a bare list of markets
        - or an object like {"data": [...]} / {"markets": [...]}
        """
        if isinstance(payload, list):
            return [m for m in payload if isinstance(m, dict)]
        if isinstance(payload, dict):
            for key in ("data", "markets"):
                val = payload.get(key)
                if isinstance(val, list):
                    return [m for m in val if isinstance(m, dict)]
        return []

    def is_sports_market(self, market: Dict) -> bool:
        sports_keywords = [
            "football", "soccer", "basketball", "baseball", "tennis",
            "hockey", "golf", "boxing", "mma", "nfl", "nba", "mlb", "nhl",
            "uefa", "fifa", "olympics", "playoff", "championship",
            "super bowl", "world cup", "premier league", "champions league",
            "sports", "game", "match", "tournament", "season", "draft",
        ]
        title = market.get("question", "").lower()
        description = market.get("description", "").lower()
        tags = [tag.lower() for tag in market.get("tags", [])]
        text_to_check = f"{title} {description} {' '.join(tags)}"
        return any(kw in text_to_check for kw in sports_keywords)

    def fetch_sports_events(self, max_results: int = 500) -> List[Dict]:
        sports_events = []
        offset = 0
        limit = 100
        print("Fetching Polymarket sports events...")
        while len(sports_events) < max_results:
            print(f"Fetching batch {offset // limit + 1}...")
            payload = self.fetch_all_markets(limit=limit, offset=offset)
            markets = self._extract_markets(payload)
            if not markets:
                break
            for market in markets:
                if self.is_sports_market(market):
                    sports_events.append(self.format_event(market))
            offset += limit
            if len(markets) < limit:
                break
        return sports_events[:max_results]

    def format_event(self, market: Dict) -> Dict:
        return {
            "id": market.get("id"),
            "question": market.get("question"),
            "description": market.get("description"),
            "end_date": market.get("endDate"),
            "end_date_iso": market.get("endDateIso"),
            "volume": market.get("volume"),
            "volume_24hr": market.get("volume24hr"),
            "liquidity": market.get("liquidity"),
            "outcomes": [
                {
                    "name": outcome.get("name"),
                    "price": outcome.get("price"),
                    "percentage": f"{float(outcome.get('price', 0)) * 100:.1f}%",
                }
                for outcome in market.get("outcomes", [])
            ],
            "tags": market.get("tags", []),
            "image": market.get("image"),
            "url": f"https://polymarket.com/event/{market.get('slug', '')}",
        }

    def save_to_json(
        self,
        events: List[Dict],
        filename: str = "polymarket_sports.json",
    ) -> None:
        with open(filename, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_events": len(events),
                "events": events,
            }, f, indent=2)
        print(f"Saved {len(events)} events to {filename}")
