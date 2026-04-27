import requests
import json
import re
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN

TELEGRAM_API_BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_message(chat_id, text, reply_markup=None):
    """Sends a message to a Telegram chat."""
    url = f"{TELEGRAM_API_BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")
        return None

def send_ev_signals(chat_id, signals):
    """Sends +EV signals with action buttons."""
    if not signals:
        send_message(chat_id, "No +EV signals available at the moment.")
        return
    
    for i, signal in enumerate(signals[:3], 1):  # Send top 3 signals
        message = f"""
🎯 <b>Signal #{i}</b>
📊 {signal['home_team']} vs {signal['away_team']}
🎲 Outcome: {signal['outcome_name']}
💰 Odds: {signal['odds']:.2f}
📈 +EV Edge: {signal['+EV_edge']:.2%}
⏰ Match Time: {signal['commence_time']}
        """
        
        # Create inline buttons
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "📋 Copy Match", "callback_data": f"copy_match_{i}"},
                    {"text": "✅ Confirm Bet", "callback_data": f"confirm_bet_{i}"}
                ]
            ]
        }
        
        send_message(chat_id, message, reply_markup)

def send_prediction_report(chat_id, shadow_balance, previous_balance, probability_of_ruin, estimated_completion_date):
    """Sends a prediction report showing simulation results."""
    balance_change = shadow_balance - previous_balance
    balance_change_pct = (balance_change / previous_balance) * 100 if previous_balance > 0 else 0
    
    message = f"""
📊 <b>Daily Prediction Report</b>

💼 Shadow Balance: ₦{shadow_balance:,.0f}
📈 Today's Growth: ₦{balance_change:,.0f} ({balance_change_pct:+.2f}%)

⚠️ Probability of Ruin: {probability_of_ruin:.2%}
🎯 Est. Completion Date: {estimated_completion_date if estimated_completion_date else 'Not reached'}

🔄 Timeline Status: {'On Track' if estimated_completion_date else 'Needs Adjustment'}
    """
    
    send_message(chat_id, message)

def parse_bank_sms(sms_text):
    """Parses bank SMS/transaction alerts for relevant keywords."""
    keywords = ['FOOTBALL.COM', 'PAYOUT', 'OPAY']
    
    for keyword in keywords:
        if keyword.upper() in sms_text.upper():
            return {
                'keyword': keyword,
                'message': sms_text,
                'timestamp': datetime.now().isoformat(),
                'category': 'Project Profit'
            }
    
    return {
        'keyword': None,
        'message': sms_text,
        'timestamp': datetime.now().isoformat(),
        'category': 'Personal/Irrelevant'
    }

def handle_forwarded_sms(chat_id, sms_text):
    """Handles forwarded bank SMS messages."""
    parsed = parse_bank_sms(sms_text)
    
    if parsed['keyword']:
        response = f"✅ Transaction logged as: {parsed['category']}\n🏷️ Keyword: {parsed['keyword']}"
    else:
        response = f"⏭️ Transaction logged as: {parsed['category']}\n(No relevant keywords found)"
    
    send_message(chat_id, response)
    return parsed

def send_scheduled_signals(chat_id, signals):
    """Sends scheduled +EV signals at 10 AM."""
    message = "🌅 <b>Morning +EV Signals</b>\n\nHere are today's top opportunities:\n"
    send_message(chat_id, message)
    send_ev_signals(chat_id, signals)

def send_scheduled_report(chat_id, report_data):
    """Sends scheduled prediction report at 9 PM."""
    send_prediction_report(
        chat_id,
        report_data['shadow_balance'],
        report_data['previous_balance'],
        report_data['probability_of_ruin'],
        report_data['estimated_completion_date']
    )

if __name__ == "__main__":
    # Example usage (for testing purposes)
    # chat_id = "YOUR_CHAT_ID"
    # test_signal = {
    #     'home_team': 'Manchester United',
    #     'away_team': 'Liverpool',
    #     'outcome_name': 'Manchester United',
    #     'odds': 2.5,
    #     '+EV_edge': 0.05,
    #     'commence_time': '2026-04-25T15:00:00Z'
    # }
    # send_ev_signals(chat_id, [test_signal])
    
    # Test SMS parsing
    test_sms = "OPAY: ₦5,000 transferred to FOOTBALL.COM. Balance: ₦95,000"
    parsed = parse_bank_sms(test_sms)
    print(f"Parsed SMS: {parsed}")
