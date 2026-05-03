import requests
import json
import re
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN
from predictive_engine import get_all_odds, identify_ev_opportunities, build_accumulator

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
        payload["reply_markup"] = json.dumps(reply_markup)

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
        sport_label = signal.get('sport_title', signal.get('sport_key', 'Unknown'))
        message = f"""
🎯 <b>Signal #{i}</b>
🏆 {sport_label}
📊 {signal['home_team']} vs {signal['away_team']}
🎲 Outcome: {signal['outcome_name']}
💰 Odds: {signal['odds']:.2f}
📈 +EV Edge: {signal['+EV_edge']:.2%}
🎯 Confidence: {signal['confidence']:.1%}
⏰ {signal['commence_time']}
        """

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "📋 Copy Match", "callback_data": f"copy_match_{i}"},
                    {"text": "✅ Confirm Bet", "callback_data": f"confirm_bet_{i}"}
                ]
            ]
        }

        send_message(chat_id, message, reply_markup)


def send_accumulator(chat_id, acca):
    """Sends an accumulator to the user."""
    if not acca:
        send_message(chat_id, "❌ Couldn't build an accumulator right now. Not enough games available.")
        return

    header = f"""
🎰 <b>ACCUMULATOR — {acca['total_odds']:.2f} ODDS</b>
━━━━━━━━━━━━━━━━━━
🎯 Target: {acca['target_odds']} odds
📊 Picks: {acca['num_picks']} selections
💰 Total: {acca['total_odds']:.2f} odds
━━━━━━━━━━━━━━━━━━
"""
    send_message(chat_id, header)

    for i, pick in enumerate(acca['picks'], 1):
        sport_label = pick.get('sport_title', pick.get('sport_key', ''))
        market_label = "Winner" if pick['market'] == 'h2h' else pick['market'].replace('_', ' ').title()

        message = f"""
<b>Pick {i}:</b>
🏆 {sport_label}
⚽ {pick['home_team']} vs {pick['away_team']}
✅ {pick['outcome_name']} ({market_label})
💰 Odds: {pick['odds']:.2f}
🎯 Confidence: {pick['confidence']:.1%}
"""
        send_message(chat_id, message)

    footer = f"""
━━━━━━━━━━━━━━━━━━
💰 <b>Combined Odds: {acca['total_odds']:.2f}</b>
💵 ₦1,000 stake → ₦{acca['total_odds'] * 1000:,.0f} potential return

⚠️ Remember: Only bet what you can afford to lose.
— Project 100k Bot
"""
    send_message(chat_id, footer)


def send_prediction_report(chat_id, shadow_balance, previous_balance, probability_of_ruin, estimated_completion_date):
    """Sends a prediction report showing simulation results."""
    balance_change = shadow_balance - previous_balance
    balance_change_pct = (balance_change / previous_balance) * 100 if previous_balance > 0 else 0

    message = f"""
📊 <b>Daily Prediction Report</b>
━━━━━━━━━━━━━━━━━━

💼 Shadow Balance: ₦{shadow_balance:,.0f}
📈 Today's Growth: ₦{balance_change:,.0f} ({balance_change_pct:+.2f}%)

⚠️ Probability of Ruin: {probability_of_ruin:.2%}
🎯 Est. Completion: {f"{estimated_completion_date:.0f} days" if estimated_completion_date else 'Not reached yet'}

🔄 Status: {'✅ On Track' if estimated_completion_date else '⚠️ Needs Adjustment'}

━━━━━━━━━━━━━━━━━━
— Project 100k Bot
    """

    send_message(chat_id, message)


def parse_bank_sms(sms_text):
    """Parses bank SMS/transaction alerts for relevant keywords."""
    keywords = ['FOOTBALL.COM', 'PAYOUT', 'OPAY']

    for keyword in keywords:
        if keyword.upper() in sms_text.upper():
            # Try to extract amount
            amount_match = re.search(r'[₦N]?([\d,]+\.?\d*)', sms_text)
            amount = amount_match.group(1).replace(',', '') if amount_match else '0'

            return {
                'keyword': keyword,
                'amount': float(amount),
                'message': sms_text,
                'timestamp': datetime.now().isoformat(),
                'category': 'Project Profit'
            }

    return {
        'keyword': None,
        'amount': 0,
        'message': sms_text,
        'timestamp': datetime.now().isoformat(),
        'category': 'Personal/Irrelevant'
    }


def handle_forwarded_sms(chat_id, sms_text):
    """Handles forwarded bank SMS messages."""
    parsed = parse_bank_sms(sms_text)

    if parsed['keyword']:
        response = f"✅ <b>Transaction logged!</b>\n\n🏷️ Keyword: {parsed['keyword']}\n💰 Amount: ₦{parsed['amount']:,.0f}\n📂 Category: {parsed['category']}"
    else:
        response = f"⏭️ <b>Skipped</b>\n\n📂 Category: {parsed['category']}\n(No relevant keywords found)"

    send_message(chat_id, response)
    return parsed


def handle_user_message(chat_id, text):
    """Handles incoming messages from the user.
    
    If the user sends a number, build an accumulator with that target odds.
    """
    text = text.strip()

    # Check if user sent a number (requesting accumulator)
    try:
        target_odds = float(text)
        if 1.5 <= target_odds <= 100:
            send_message(chat_id, f"🔍 Building you a ~{target_odds:.0f} odds accumulator...\nScanning all sports...")
            
            all_odds = get_all_odds()
            acca = build_accumulator(target_odds, all_odds)
            send_accumulator(chat_id, acca)
            return
        else:
            send_message(chat_id, "⚠️ Please send a number between 1.5 and 100 for target odds.")
            return
    except ValueError:
        pass

    # Check for commands
    if text.lower() in ['/start', 'start']:
        welcome = """
🟢 <b>Project 100k Bot</b>
━━━━━━━━━━━━━━━━━━

Welcome! Here's what I can do:

📊 <b>Auto Signals:</b> I send +EV picks at 10 AM and reports at 9 PM daily.

🎰 <b>Accumulator:</b> Send me any number (like 5, 10, 20) and I'll build you an accumulator with that target odds.

💳 <b>Bank SMS:</b> Forward me your transaction alerts and I'll sort them (Project Profit vs Personal).

<b>Commands:</b>
• Send a number → Get accumulator
• Forward SMS → Auto-categorize
• /signals → Get current +EV signals
• /report → Get prediction report now

━━━━━━━━━━━━━━━━━━
— Project 100k Bot
"""
        send_message(chat_id, welcome)
        return

    if text.lower() in ['/signals', 'signals']:
        send_message(chat_id, "🔍 Scanning all sports for +EV opportunities...")
        all_odds = get_all_odds()
        if all_odds:
            ev_opps = identify_ev_opportunities(all_odds)
            if ev_opps:
                send_ev_signals(chat_id, ev_opps)
            else:
                send_message(chat_id, "No +EV opportunities found right now. Try again later.")
        else:
            send_message(chat_id, "❌ Couldn't fetch odds. API might be down.")
        return

    # If it looks like a forwarded SMS (contains money-related words)
    money_indicators = ['credit', 'debit', 'transfer', 'received', 'sent', 'balance', '₦', 'NGN']
    if any(indicator.lower() in text.lower() for indicator in money_indicators):
        handle_forwarded_sms(chat_id, text)
        return

    # Default response
    send_message(chat_id, "Send me a number (like 5, 10, 20) to get an accumulator with that target odds.\n\nOr type /signals for current +EV picks.")


def send_scheduled_signals(chat_id, signals):
    """Sends scheduled +EV signals at 10 AM."""
    message = "🌅 <b>Morning +EV Signals</b>\n━━━━━━━━━━━━━━━━━━\nHere are today's top opportunities across all sports:\n"
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


def get_updates(offset=None):
    """Gets new messages sent to the bot."""
    url = f"{TELEGRAM_API_BASE_URL}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting updates: {e}")
        return None


def run_bot_polling():
    """Runs the bot in polling mode to listen for messages."""
    print("Bot is running... Listening for messages.")
    offset = None

    while True:
        updates = get_updates(offset)
        if updates and updates.get('ok'):
            for update in updates.get('result', []):
                offset = update['update_id'] + 1

                # Handle regular messages
                if 'message' in update:
                    message = update['message']
                    chat_id = message['chat']['id']
                    text = message.get('text', '')

                    if text:
                        print(f"Received from {chat_id}: {text}")
                        handle_user_message(str(chat_id), text)

                # Handle callback queries (button presses)
                elif 'callback_query' in update:
                    callback = update['callback_query']
                    chat_id = callback['message']['chat']['id']
                    data = callback.get('data', '')
                    
                    # Acknowledge the callback
                    requests.post(
                        f"{TELEGRAM_API_BASE_URL}/answerCallbackQuery",
                        json={"callback_query_id": callback['id'], "text": "✅ Noted!"}
                    )


if __name__ == "__main__":
    run_bot_polling()
