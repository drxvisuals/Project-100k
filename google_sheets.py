import gspread
from datetime import datetime
from config import GOOGLE_SHEETS_CREDENTIALS, SPREADSHEET_ID

def init_google_sheet():
    """Initializes connection to Google Sheets and creates/opens the spreadsheet."""
    if not GOOGLE_SHEETS_CREDENTIALS:
        print("Google Sheets credentials not configured.")
        return None
    
    try:
        gc = gspread.service_account(filename=GOOGLE_SHEETS_CREDENTIALS)
        spreadsheet = gc.open_by_id(SPREADSHEET_ID)
        print(f"Successfully connected to Google Sheet: {spreadsheet.title}")
        return spreadsheet
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None

def get_worksheet(spreadsheet, worksheet_name="Simulation_Logs"):
    """Gets a worksheet by name, creating it if it doesn't exist."""
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
        print(f"Successfully opened worksheet: {worksheet_name}")
        return worksheet
    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{worksheet_name}' not found. Creating it...")
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows="100", cols="10")
        # Set up headers
        headers = ["Date", "Match", "Odds", "Actual_Bet", "Simulated_Bet", "Result", "Current_Equity"]
        worksheet.append_row(headers)
        print(f"Worksheet '{worksheet_name}' created with headers.")
        return worksheet
    except Exception as e:
        print(f"Error getting/creating worksheet: {e}")
        return None

def log_simulation_result(worksheet, date, match, odds, actual_bet, simulated_bet, result, current_equity):
    """Logs a single simulation result to the Google Sheet."""
    try:
        row = [date, match, odds, actual_bet, simulated_bet, result, current_equity]
        worksheet.append_row(row)
        print(f"Logged simulation result: {row}")
        return True
    except Exception as e:
        print(f"Error logging simulation result: {e}")
        return False

if __name__ == "__main__":
    # This part requires GOOGLE_SHEETS_CREDENTIALS and SPREADSHEET_ID to be set in config.py
    # For local testing, you would need to set up a service account and share the sheet with it.
    # Example usage:
    # spreadsheet = init_google_sheet()
    # if spreadsheet:
    #     worksheet = get_worksheet(spreadsheet)
    #     if worksheet:
    #         log_simulation_result(worksheet, str(datetime.now()), "Team A vs Team B", 2.5, 100, 100, "Win", 5100)
    pass
