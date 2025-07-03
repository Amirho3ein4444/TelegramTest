import os
import requests
import json

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
OWNER_CHAT_ID = os.environ.get('OWNER_CHAT_ID')
GREETING_MESSAGE = "سلام من آماده ام که پیامتو بخونم"

def send_telegram_message(chat_id, text):
    """A helper function to send a message using the Telegram Bot API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, json=payload)
    return response.json()

def main(context):
    """
    This is the main function that Appwrite will run.
    """
    # ⭐️ FIX: First, check if there is any data in the request body.
    if not context.req.body:
        context.log("Manual execution or empty request body. Skipping.")
        return context.res.json({'status': 'ok, no data'})

    try:
        # Now we can safely parse the JSON
        update = json.loads(context.req.body)
        context.log(f"Received update: {update}")

        if 'message' in update and 'text' in update['message']:
            message = update['message']
            chat_id = message['chat']['id']
            text = message['text']
            
            sender_info = message['from']
            sender_name = sender_info.get('first_name', '')
            if sender_info.get('last_name'):
                sender_name += f" {sender_info.get('last_name')}"
            sender_username = sender_info.get('username', 'N/A')
            sender_id = sender_info['id']

            # --- LOGIC FOR THE BOT ---
            if text == '/start':
                context.log(f"User {sender_name} started the bot. Sending greeting.")
                send_telegram_message(chat_id, GREETING_MESSAGE)
                
                notification_text = f"✅ New user started the bot:\nName: {sender_name}\nUsername: @{sender_username}\nUser ID: {sender_id}"
                send_telegram_message(OWNER_CHAT_ID, notification_text)
            else:
                context.log(f"Forwarding message from {sender_name} to owner.")
                forwarded_message = (
                    f"📩 New message from {sender_name} (@{sender_username}):\n\n"
                    f'"{text}"\n\n'
                    f"Reply to this user by sending a message to chat ID: {chat_id}"
                )
                send_telegram_message(OWNER_CHAT_ID, forwarded_message)

        return context.res.json({'status': 'ok'})

    except Exception as e:
        context.error(f"An error occurred: {e}")
        return context.res.json({'status': 'error handled'})
