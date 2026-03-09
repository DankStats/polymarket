# Polymarket sports × bookmaker odds

Scrape sport events from [Polymarket](https://polymarket.com) and cross them with real odds from major bookmakers (via [The Odds API](https://the-odds-api.com)).

## Layout

- **main.py** – CLI entry point (run this or `Py01_main.py`)
- **polymarket_api.py** – Polymarket Gamma API client
- **bookmaker_api.py** – The Odds API client
- **crossing.py** – match events and compare implied probabilities

## Setup

```bash
pip install -r requirements.txt
```

**Bookmaker odds (optional)**  
Get a free API key from [The Odds API](https://the-odds-api.com) (500 requests/month on free tier).  
Set it when running:

```bash
export THE_ODDS_API_KEY=your_key_here
```

*Note: Bet365 is not in The Odds API; you get other major bookmakers (Betfair, Paddy Power, Sky Bet, Ladbrokes, etc.). For Bet365 specifically you’d need another provider (e.g. odds-api.io).*

## Run

From the project directory:

**Only Polymarket sports events**

```bash
python main.py
```

**Polymarket + cross with bookmaker odds**

```bash
python main.py --cross
```

You can also run `python Py01_main.py` (same behaviour).

**Options**

- `--max 200` – max Polymarket events to fetch (default 200)
- `--cross` – fetch bookmaker odds and match to Polymarket events
- `--region uk` – bookmaker region: `uk`, `us`, `eu`, `au`

## Output

- **polymarket_sports.json** – Polymarket sports events (always)
- **polymarket_vs_bookmaker.json** – matched events and outcome comparison when using `--cross`

Comparison shows, per outcome:

- Polymarket implied probability (from market price)
- Bookmaker implied probability (1 / best decimal odds across bookmakers)
- “Value” flag when Polymarket price is lower than bookmaker-implied (potential value on Polymarket)
