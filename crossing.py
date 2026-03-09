"""Match Polymarket events to bookmaker events and compare implied probabilities."""

import re
from typing import Dict, List

from bookmaker_api import BookmakerOddsAPI


def normalize_name(s: str) -> str:
    """Lowercase, collapse spaces, remove common suffixes for matching."""
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    for x in [" fc", " cf", " united", " city", " fc.", " cf."]:
        s = s.replace(x, "")
    return s


def team_names_in_text(team_list: List[str], text: str) -> bool:
    """True if all teams appear in text (fuzzy)."""
    if not team_list or not text:
        return False
    text_n = normalize_name(text)
    for t in team_list:
        if not t:
            continue
        tn = normalize_name(t)
        if tn not in text_n:
            short = tn.split()[0] if tn else ""
            if short and len(short) >= 3 and short not in text_n:
                return False
    return True


def cross_polymarket_with_bookmaker(
    polymarket_events: List[Dict],
    bookmaker_events: List[Dict],
) -> List[Dict]:
    """
    Match Polymarket sports events to bookmaker events by team names.
    Returns list of { polymarket_event, bookmaker_event, best_odds, comparison }.
    """
    results = []
    for pe in polymarket_events:
        q = (pe.get("question") or "") + " " + (pe.get("description") or "")
        for be in bookmaker_events:
            teams = be.get("teams", [])
            if len(teams) < 2:
                continue
            if not team_names_in_text(teams, q):
                continue
            best = BookmakerOddsAPI.best_odds_by_outcome(be)
            if not best:
                continue
            poly_outcomes = pe.get("outcomes", [])
            comparison = []
            for i, out in enumerate(poly_outcomes):
                name = (out.get("name") or "").strip()
                price = float(out.get("price") or 0)
                poly_pct = price * 100
                bm_pct = None
                bm_odds = None
                for bm_key, bm_odd in best.items():
                    if name and normalize_name(name) in normalize_name(bm_key):
                        bm_pct = 100.0 / bm_odd
                        bm_odds = bm_odd
                        break
                if bm_pct is None and i < len(teams):
                    bm_key = teams[i] if i < len(teams) else list(best.keys())[i]
                    if bm_key in best:
                        bm_odds = best[bm_key]
                        bm_pct = 100.0 / bm_odds
                if bm_pct is not None and bm_odds is not None:
                    diff = poly_pct - bm_pct
                    comparison.append({
                        "outcome": name or f"Outcome{i}",
                        "polymarket_prob": round(poly_pct, 1),
                        "bookmaker_implied_prob": round(bm_pct, 1),
                        "bookmaker_best_odds": round(bm_odds, 2),
                        "diff_pct_points": round(diff, 1),
                        "value_on_polymarket": diff < -2,
                    })
            results.append({
                "polymarket_event": pe,
                "bookmaker_event": {
                    "teams": be.get("teams"),
                    "sport": be.get("sport_nice"),
                    "commence_time": be.get("commence_time"),
                },
                "best_odds": best,
                "comparison": comparison,
            })
            break
    return results
