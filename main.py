import time
import schedule
from datetime import datetime
from predictive_engine import get_odds, identify_ev_opportunities, run_monte_carlo_simulation
from telegram_bot import send_scheduled_signals, send_scheduled_report
from google_sheets import init_google_sheet, get_worksheet, log_simulation_result

# Configuration for chat_id (this should be the user's chat ID)
USER_CHAT_ID = "636252445" # Placeholder - user should provide their actual chat ID

def morning_task():
    """Task to run at 10 AM."""
    print(f"Running morning task at {datetime.now()}")
    odds = get_odds()
    if odds:
        ev_opportunities = identify_ev_opportunities(odds)
        if ev_opportunities:
            send_scheduled_signals(USER_CHAT_ID, ev_opportunities)
        else:
            print("No +EV opportunities found this morning.")
    else:
        print("Failed to fetch odds this morning.")

def evening_task():
    """Task to run at 9 PM."""
    print(f"Running evening task at {datetime.now()}")
    
    # Run simulation for the report
    # In a real scenario, this would use actual data from the day's results
    current_equity = 5000 # This should be fetched from session state or database
    previous_equity = 4900 # Placeholder for yesterday's balance
    
    simulation_results = run_monte_carlo_simulation(current_equity)
    
    report_data = {
        'shadow_balance': current_equity,
        'previous_balance': previous_equity,
        'probability_of_ruin': simulation_results['probability_of_ruin'],
        'estimated_completion_date': simulation_results['estimated_completion_date']
    }
    
    send_scheduled_report(USER_CHAT_ID, report_data)
    
    # Log to Google Sheets
    spreadsheet = init_google_sheet()
    if spreadsheet:
        worksheet = get_worksheet(spreadsheet)
        if worksheet:
            log_simulation_result(
                worksheet,
                datetime.now().strftime("%Y-%m-%d"),
                "Daily Summary",
                0, # Odds N/A
                0, # Actual Bet N/A
                0, # Simulated Bet N/A
                "N/A",
                current_equity
            )

def run_scheduler():
    """Main loop for the background scheduler."""
    schedule.every().day.at("10:00").do(morning_task)
    schedule.every().day.at("21:00").do(evening_task)
    
    print("Scheduler started. Waiting for tasks...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # For testing, you can run tasks immediately
    # morning_task()
    # evening_task()
    
    run_scheduler()
