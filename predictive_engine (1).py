import requests
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from itertools import combinations

from config import ODDS_API_KEY

# The Odds API configuration
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4/sports"
ODDS_FORMAT = "decimal"
DATE_FORMAT = "iso"
REGIONS = "uk,eu"

# All supported sports for +EV scanning
SPORTS = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",
    "soccer_uefa_champs_league",
    "basketball_nba",
    "basketball_euroleague",
    "tennis_atp_french_open",
    "americanfootball_nfl",
    "icehockey_nhl",
    "mma_mixed_martial_arts",
]

# Markets to scan
MARKETS = "h2h,totals"


def get_available_sports():
    """Fetches all available sports from The Odds API."""
    url = f"{ODDS_API_BASE_URL}"
    params = {"apiKey": ODDS_API_KEY}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sports: {e}")
        return []


def get_odds(sport_key="soccer_epl"):
    """Fetches odds from The Odds API for a specific sport."""
    url = f"{ODDS_API_BASE_URL}/{sport_key}/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
        "dateFormat": DATE_FORMAT,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching odds for {sport_key}: {e}")
        return None


def get_all_odds():
    """Fetches odds across all supported sports."""
    all_odds = []
    for sport in SPORTS:
        odds = get_odds(sport)
        if odds:
            for event in odds:
                event['sport_key'] = sport
            all_odds.extend(odds)
    return all_odds


def identify_ev_opportunities(odds_data):
    """Identifies +EV opportunities from fetched odds across all sports."""
    ev_opportunities = []
    if odds_data:
        for event in odds_data:
            bookmaker_odds = {}
            for bookmaker in event.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    for outcome in market.get('outcomes', []):
                        key = f"{market['key']}_{outcome['name']}"
                        if key not in bookmaker_odds:
                            bookmaker_odds[key] = []
                        bookmaker_odds[key].append({
                            'bookmaker': bookmaker['title'],
                            'price': outcome.get('price', 0),
                            'market': market['key'],
                            'outcome_name': outcome['name']
                        })

            # Find +EV by comparing across bookmakers
            for key, odds_list in bookmaker_odds.items():
                if len(odds_list) >= 2:
                    prices = [o['price'] for o in odds_list]
                    max_price = max(prices)
                    avg_price = sum(prices) / len(prices)
                    implied_prob = 1 / avg_price
                    best_implied = 1 / max_price

                    # If best odds are significantly better than average
                    edge = (implied_prob - best_implied) / best_implied
                    if edge > 0.03:  # 3% edge minimum
                        best_odd = odds_list[prices.index(max_price)]
                        ev_opportunities.append({
                            'event_id': event.get('id', ''),
                            'sport_key': event.get('sport_key', event.get('sport_title', '')),
                            'sport_title': event.get('sport_title', ''),
                            'commence_time': event.get('commence_time', ''),
                            'home_team': event.get('home_team', ''),
                            'away_team': event.get('away_team', ''),
                            'bookmaker': best_odd['bookmaker'],
                            'market': best_odd['market'],
                            'outcome_name': best_odd['outcome_name'],
                            'odds': max_price,
                            'implied_probability': best_implied,
                            'avg_probability': implied_prob,
                            '+EV_edge': edge,
                            'confidence': min(0.95, implied_prob * (1 + edge))
                        })

    # Sort by confidence (highest first)
    ev_opportunities.sort(key=lambda x: x['confidence'], reverse=True)
    return ev_opportunities


def build_accumulator(target_odds, odds_data=None):
    """Builds an accumulator that totals approximately the target odds.
    
    Uses the highest-confidence picks to build a safe accumulator.
    """
    if odds_data is None:
        odds_data = get_all_odds()

    if not odds_data:
        return None

    # Get all available picks with their confidence scores
    picks = []
    for event in odds_data:
        for bookmaker in event.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                for outcome in market.get('outcomes', []):
                    price = outcome.get('price', 0)
                    if 1.1 <= price <= 5.0:  # Reasonable odds range for accumulators
                        implied_prob = 1 / price
                        picks.append({
                            'event_id': event.get('id', ''),
                            'sport_key': event.get('sport_key', event.get('sport_title', '')),
                            'sport_title': event.get('sport_title', ''),
                            'commence_time': event.get('commence_time', ''),
                            'home_team': event.get('home_team', ''),
                            'away_team': event.get('away_team', ''),
                            'bookmaker': bookmaker['title'],
                            'market': market['key'],
                            'outcome_name': outcome['name'],
                            'odds': price,
                            'confidence': implied_prob,
                            'description': outcome.get('description', '')
                        })

    if not picks:
        return None

    # Remove duplicate events (only keep best odds per event+outcome)
    seen_events = {}
    for pick in picks:
        key = f"{pick['event_id']}_{pick['market']}_{pick['outcome_name']}"
        if key not in seen_events or pick['odds'] > seen_events[key]['odds']:
            seen_events[key] = pick

    unique_picks = list(seen_events.values())

    # Sort by confidence (safest first)
    unique_picks.sort(key=lambda x: x['confidence'], reverse=True)

    # Greedy algorithm: build accumulator to reach target odds
    selected = []
    current_total_odds = 1.0
    used_events = set()

    for pick in unique_picks:
        if current_total_odds >= target_odds:
            break

        # Don't use same event twice
        event_key = f"{pick['home_team']}_{pick['away_team']}"
        if event_key in used_events:
            continue

        # Check if adding this pick overshoots too much
        potential_odds = current_total_odds * pick['odds']
        if potential_odds > target_odds * 1.5 and len(selected) > 0:
            continue

        selected.append(pick)
        current_total_odds *= pick['odds']
        used_events.add(event_key)

    if not selected:
        return None

    return {
        'picks': selected,
        'total_odds': current_total_odds,
        'num_picks': len(selected),
        'target_odds': target_odds
    }


def run_monte_carlo_simulation(initial_balance, num_simulations=1000, num_days=30, avg_daily_return=0.01, daily_volatility=0.02):
    """Runs a Monte Carlo simulation to forecast balance and calculate risk metrics."""
    simulated_balances = np.zeros((num_simulations, num_days))
    probability_of_ruin = 0
    completion_dates = []

    for i in range(num_simulations):
        balance = initial_balance
        daily_returns = np.random.normal(avg_daily_return, daily_volatility, num_days)

        for day in range(num_days):
            balance *= (1 + daily_returns[day])
            simulated_balances[i, day] = balance
            if balance <= 0:
                probability_of_ruin += 1
                break
            if balance >= 100000:  # Goal balance
                completion_dates.append(day + 1)
                break

    probability_of_ruin /= num_simulations

    # Calculate 90% Confidence Interval
    lower_bound = np.percentile(simulated_balances[:, -1], 5)
    upper_bound = np.percentile(simulated_balances[:, -1], 95)

    estimated_completion_date = None
    if completion_dates:
        estimated_completion_date = np.mean(completion_dates)

    return {
        "simulated_balances": simulated_balances,
        "probability_of_ruin": probability_of_ruin,
        "estimated_completion_date": estimated_completion_date,
        "confidence_interval": (lower_bound, upper_bound)
    }


if __name__ == "__main__":
    print("Fetching odds across all sports...")
    all_odds = get_all_odds()
    if all_odds:
        print(f"Fetched {len(all_odds)} events across all sports.")
        ev_opportunities = identify_ev_opportunities(all_odds)
        print(f"Identified {len(ev_opportunities)} +EV opportunities.")

        print("\nBuilding 10-odds accumulator...")
        acca = build_accumulator(10.0, all_odds)
        if acca:
            print(f"Accumulator: {acca['num_picks']} picks, total odds: {acca['total_odds']:.2f}")
            for pick in acca['picks']:
                print(f"  {pick['home_team']} vs {pick['away_team']} | {pick['outcome_name']} @ {pick['odds']:.2f}")
