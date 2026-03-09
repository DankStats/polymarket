"""CLI entry point: fetch Polymarket sports and optionally cross with bookmaker odds."""

import argparse
import json
import os
from datetime import datetime

import requests

from polymarket_api import PolymarketSportsAPI
from bookmaker_api import BookmakerOddsAPI
from crossing import cross_polymarket_with_bookmaker


def run(max_events: int, cross: bool, region: str) -> None:
    api = PolymarketSportsAPI()
    sports_events = api.fetch_sports_events(max_results=max_events)

    print(f"\nFound {len(sports_events)} sports events:")
    print("-" * 50)
    for i, event in enumerate(sports_events[:10], 1):
        print(f"{i}. {event['question']}")
        print(f"   End Date: {event['end_date']}")
        vol = event.get("volume_24hr")
        print(f"   Volume (24h): ${vol:,.2f}" if vol else "   Volume (24h): N/A")
        outcomes_str = ", ".join(f"{o['name']}: {o['percentage']}" for o in event["outcomes"])
        print(f"   Outcomes: {outcomes_str}")
        print()

    api.save_to_json(sports_events)

    total_volume = sum(float(event.get("volume_24hr") or 0) for event in sports_events)
    print(f"\nSummary: {len(sports_events)} events, 24h volume ${total_volume:,.2f}")

    if not cross:
        return

    odds_key = os.environ.get("THE_ODDS_API_KEY")
    if not odds_key:
        print("\nSkipping cross: set THE_ODDS_API_KEY to cross with bookmaker odds.")
        return

    print("\nFetching bookmaker odds (The Odds API)...")
    odds_api = BookmakerOddsAPI()
    try:
        bookmaker_events = odds_api.get_odds_upcoming(region=region)
    except requests.RequestException as e:
        print(f"Odds API error: {e}")
        bookmaker_events = []

    if not bookmaker_events:
        print("No bookmaker events returned (check key and quota).")
        return

    crossed = cross_polymarket_with_bookmaker(sports_events, bookmaker_events)
    print(f"Matched {len(crossed)} Polymarket events to bookmaker odds.\n")
    for c in crossed[:15]:
        pe = c["polymarket_event"]
        be = c["bookmaker_event"]
        print(f"  {pe.get('question', '')[:70]}...")
        print(f"    Teams: {be.get('teams')} | Sport: {be.get('sport')}")
        print(f"    Best odds: {c['best_odds']}")
        for comp in c.get("comparison", []):
            v = " [VALUE]" if comp.get("value_on_polymarket") else ""
            print(f"      {comp['outcome']}: Polymarket {comp['polymarket_prob']}% vs bookmaker {comp['bookmaker_implied_prob']}% (odds {comp['bookmaker_best_odds']}){v}")
        print()

    out_path = "polymarket_vs_bookmaker.json"
    with open(out_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "matched": len(crossed),
            "comparisons": [
                {
                    "question": c["polymarket_event"].get("question"),
                    "url": c["polymarket_event"].get("url"),
                    "bookmaker_teams": c["bookmaker_event"].get("teams"),
                    "best_odds": c["best_odds"],
                    "comparison": c["comparison"],
                }
                for c in crossed
            ],
        }, f, indent=2)
    print(f"Saved comparisons to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Polymarket sports + cross with bookmaker odds"
    )
    parser.add_argument(
        "--max",
        type=int,
        default=200,
        help="Max Polymarket events to fetch",
    )
    parser.add_argument(
        "--cross",
        action="store_true",
        help="Cross with bookmaker odds (requires THE_ODDS_API_KEY)",
    )
    parser.add_argument(
        "--region",
        default="uk",
        choices=["uk", "us", "eu", "au"],
        help="Bookmaker region",
    )
    args = parser.parse_args()
    run(args.max, args.cross, args.region)


if __name__ == "__main__":
    main()
