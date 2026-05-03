import time
import threading
import schedule
from datetime import datetime
from predictive_engine import get_all_odds, identify_ev_opportunities, run_monte_carlo_simulation
from telegram_bot import send_scheduled_signals, send_scheduled_report, run_bot_polling
from google_sheets import init_google_sheet, get_worksheet, log_simulation_result

# Your Telegram chat ID
USER_CHAT_ID = "7597264532"


def morning_task():
    """Task to run at 10 AM — sends +EV signals across all sports."""
    print(f"Running morning task at {datetime.now()}")
    all_odds = get_all_odds()
    if all_odds:
        ev_opportunities = identify_ev_opportunities(all_odds)
        if ev_opportunities:
            send_scheduled_signals(USER_CHAT_ID, ev_opportunities)
            print(f"Sent {len(ev_opportunities[:3])} signals.")
        else:
            print("No +EV opportunities found this morning.")
    else:
        print("Failed to fetch odds this morning.")


def evening_task():
    """Task to run at 9 PM — sends prediction report."""
    print(f"Running evening task at {datetime.now()}")

    current_equity = 5000
    previous_equity = 4900

    simulation_results = run_monte_carlo_simulation(current_equity)

    report_data = {
        'shadow_balance': current_equity,
        'previous_balance': previous_equity,
        'probability_of_ruin': simulation_results['probability_of_ruin'],
        'estimated_completion_date': simulation_results['estimated_completion_date']
    }

    send_scheduled_report(USER_CHAT_ID, report_data)

    spreadsheet = init_google_sheet()
    if spreadsheet:
        worksheet = get_worksheet(spreadsheet)
        if worksheet:
            log_simulation_result(
                worksheet,
                datetime.now().strftime("%Y-%m-%d"),
                "Daily Summary",
                0,
                0,
                0,
                "N/A",
                current_equity
            )


def run_scheduler():
    """Background thread for scheduled tasks."""
    schedule.every().day.at("10:00").do(morning_task)
    schedule.every().day.at("21:00").do(evening_task)

    print("Scheduler started. 10 AM signals + 9 PM reports.")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    print("=" * 40)
    print("PROJECT 100k BOT")
    print("=" * 40)
    print(f"Started at: {datetime.now()}")
    print(f"Chat ID: {USER_CHAT_ID}")
    print("Features:")
    print("  - Auto +EV signals at 10 AM")
    print("  - Prediction report at 9 PM")
    print("  - Interactive accumulator (send any number)")
    print("  - Bank SMS parser")
    print("=" * 40)

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    run_bot_polling()
