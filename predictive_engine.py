import requests
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from config import ODDS_API_KEY

# The Odds API configuration
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4/sports"
SPORT_KEY = "soccer_epl"  # Example: English Premier League soccer
REGIONS = "uk"  # Example: UK bookmakers
MARKETS = "h2h"  # Head-to-head odds
ODDS_FORMAT = "decimal"
DATE_FORMAT = "iso"

def get_odds():
    """Fetches odds from The Odds API."""
    url = f"{ODDS_API_BASE_URL}/{SPORT_KEY}/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
        "dateFormat": DATE_FORMAT,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        odds_data = response.json()
        return odds_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching odds: {e}")
        return None

def identify_ev_opportunities(odds_data):
    """Identifies +EV opportunities from fetched odds."""
    ev_opportunities = []
    if odds_data:
        for event in odds_data:
            for bookmaker in event.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'h2h':
                        for outcome in market.get('outcomes', []):
                            price = outcome.get('price')
                            if price:
                                # Calculate implied probability
                                implied_probability = 1 / price
                                # Placeholder for model's estimated probability
                                # For now, let's assume a simple model that finds a small edge
                                model_probability = implied_probability * 1.05 # Assume a 5% edge for demonstration

                                if model_probability > implied_probability:
                                    ev_opportunities.append({
                                        'event_id': event['id'],
                                        'sport_title': event['sport_title'],
                                        'commence_time': event['commence_time'],
                                        'home_team': event['home_team'],
                                        'away_team': event['away_team'],
                                        'bookmaker': bookmaker['title'],
                                        'market': market['key'],
                                        'outcome_name': outcome['name'],
                                        'odds': price,
                                        'implied_probability': implied_probability,
                                        'model_probability': model_probability,
                                        '+EV_edge': (model_probability - implied_probability) / implied_probability
                                    })
    return ev_opportunities

def verify_match_score(match_id, kickoff_time):
    """Placeholder for autonomous verification of match scores via Flashscore/LiveScore.
    This will involve browsing Flashscore/LiveScore 2 hours after kickoff to get the final score.
    """
    print(f"Verifying match {match_id} score after {kickoff_time + timedelta(hours=2)}...")
    # TODO: Implement actual browsing logic here
    # For now, we'll simulate a score. Actual browsing will be implemented later.
    return "2-1"

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
            if balance >= 100000: # Goal balance
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
    # Example usage of verification (for testing purposes)
    # from datetime import datetime, timedelta
    # match_id_example = "some_match_id_123"
    # kickoff_time_example = datetime.now() - timedelta(hours=3) # Simulate a match that ended 3 hours ago
    # verified_score = verify_match_score(match_id_example, kickoff_time_example)
    # print(f"Verified score for {match_id_example}: {verified_score}")


    print("Fetching odds...")
    odds = get_odds()
    if odds:
        print(f"Fetched {len(odds)} events.")
        # print(json.dumps(odds[0], indent=2)) # Print first event for inspection
        ev_opportunities = identify_ev_opportunities(odds)
        print(f"Identified {len(ev_opportunities)} +EV opportunities (placeholder).")

    print("\nRunning Monte Carlo simulation...")
    initial_balance = 5000
    simulation_results = run_monte_carlo_simulation(initial_balance)
    print(f"Probability of Ruin: {simulation_results['probability_of_ruin']:.2%}")
    if simulation_results['estimated_completion_date']:
        print(f"Estimated Completion Date: {simulation_results['estimated_completion_date']:.0f} days")
    else:
        print("Estimated Completion Date: Not reached within simulation period")
    print(f"90% Confidence Interval for final balance: ₦{simulation_results['confidence_interval'][0]:.2f} - ₦{simulation_results['confidence_interval'][1]:.2f}")
