"""Bookmaker odds via The Odds API (the-odds-api.com)."""

import os
import requests
from typing import Dict, List, Optional


class BookmakerOddsAPI:
    """Fetch odds from The Odds API. Free tier: 500 req/month."""

    BASE = "https://api.the-odds-api.com/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("THE_ODDS_API_KEY", "")
        self.session = requests.Session()

    def get_sports(self, all_sports: bool = False) -> List[Dict]:
        """List in-season sports (no quota cost). Use returned 'key' for odds requests."""
        params = {"apiKey": self.api_key}
        if all_sports:
            params["all"] = "true"
        r = self.session.get(f"{self.BASE}/sports", params=params)
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            return []
        return data.get("data", [])

    def get_odds(
        self,
        sport_key: str,
        region: str = "uk",
        mkt: str = "h2h",
    ) -> List[Dict]:
        """Get upcoming events and odds for a sport. region: uk, us, eu, au."""
        params = {
            "apiKey": self.api_key,
            "sport": sport_key,
            "region": region,
            "mkt": mkt,
        }
        r = self.session.get(f"{self.BASE}/odds", params=params)
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            return []
        return data.get("data", [])

    def get_odds_upcoming(
        self,
        region: str = "uk",
        mkt: str = "h2h",
    ) -> List[Dict]:
        """Get next upcoming games across all sports (uses quota)."""
        params = {
            "apiKey": self.api_key,
            "sport": "upcoming",
            "region": region,
            "mkt": mkt,
        }
        r = self.session.get(f"{self.BASE}/odds", params=params)
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            return []
        return data.get("data", [])

    @staticmethod
    def best_odds_by_outcome(event: Dict) -> Dict[str, float]:
        """Best decimal odds per outcome (h2h: home, away, [draw])."""
        teams = event.get("teams", [])
        home = event.get("home_team") or (teams[0] if teams else "Home")
        away = teams[1] if len(teams) > 1 else "Away"
        sites = event.get("sites", [])
        best = {}
        for site in sites:
            odds = (site.get("odds") or {}).get("h2h")
            if not odds:
                continue
            labels = [home, away] if len(odds) == 2 else [home, "Draw", away]
            for i, dec in enumerate(odds):
                if i >= len(labels):
                    break
                key = labels[i]
                if key not in best or dec > best[key]:
                    best[key] = float(dec)
        return best
