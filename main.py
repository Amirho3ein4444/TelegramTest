import os
import requests
import json

# --- CONFIGURATION ---
# These will be set in your Appwrite Function's Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
# This is your personal Telegram user ID, where the bot will send messages.
OWNER_CHAT_ID = os.environ.get('OWNER_CHAT_ID')

# The greeting message in Persian
GREETING_MESSAGE = "سلام من آماده ام که پیامتو بخونم"

def send_telegram_message(chat_id, text):
    """A helper function to send a message using the Telegram Bot API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    # We use requests.post and send data as json
    response = requests.post(url, json=payload)
    return response.json()

def main(context):
    """
    This is the main function that Appwrite will run when Telegram sends a notification.
    """
    # The data from Telegram comes in the request body
    try:
        # Parse the JSON payload from Telegram
        update = json.loads(context.req.body)
        context.log(f"Received update: {update}")

        # Check if the update contains a message with text
        if 'message' in update and 'text' in update['message']:
            message = update['message']
            chat_id = message['chat']['id']
            text = message['text']
            
            # Get information about the sender
            sender_info = message['from']
            sender_name = sender_info.get('first_name', '')
            if sender_info.get('last_name'):
                sender_name += f" {sender_info.get('last_name')}"
            sender_username = sender_info.get('username', 'N/A')
            sender_id = sender_info['id']

            # --- LOGIC FOR THE BOT ---

            # 1. If the user sends "/start", send the greeting message back to them.
            if text == '/start':
                context.log(f"User {sender_name} started the bot. Sending greeting.")
                send_telegram_message(chat_id, GREETING_MESSAGE)
                
                # Also notify the owner that a new user has started the bot
                notification_text = f"✅ New user started the bot:\nName: {sender_name}\nUsername: @{sender_username}\nUser ID: {sender_id}"
                send_telegram_message(OWNER_CHAT_ID, notification_text)

            # 2. For any other message, forward it to the owner.
            else:
                context.log(f"Forwarding message from {sender_name} to owner.")
                
                # Create a nicely formatted message to forward
                forwarded_message = (
                    f"📩 New message from {sender_name} (@{sender_username}):\n\n"
                    f'"{text}"\n\n'
                    f"Reply to this user by sending a message to chat ID: {chat_id}"
                )
                
                send_telegram_message(OWNER_CHAT_ID, forwarded_message)

        return context.res.json({'status': 'ok'})

    except Exception as e:
        context.error(f"An error occurred: {e}")
        # It's good practice to still return a success status to Telegram
        # so it doesn't keep trying to send the same failed update.
        return context.res.json({'status': 'error handled'})

