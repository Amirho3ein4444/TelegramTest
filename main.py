import os
import json
import requests
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from appwrite.query import Query

# --- Appwrite Configuration ---
APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY")
APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
APPWRITE_DATABASE_ID = "6865a12e0028549f1ee0"  # Replace with your Appwrite Database ID
APPWRITE_COLLECTION_ID = "6865a159003230cf8118" # Replace with your Appwrite Collection ID

# --- Telegram Configuration ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "-1001953596222"  # Replace with your Telegram Channel ID
SOURCE_CHANNELS = ["@drtel18", "esteghlaal_twitter"] # Replace with the source channel usernames or IDs

# --- OpenRouter Configuration ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
YOUR_SITE_URL = "http://localhost"  # Replace with your website or a placeholder
YOUR_APP_NAME = "Telegram Bot"

def main(context):
    """
    Main function to be executed by Appwrite.
    """
    # Initialize Appwrite client
    client = Client()
    client.set_endpoint(APPWRITE_ENDPOINT)
    client.set_project(APPWRITE_PROJECT_ID)
    client.set_key(APPWRITE_API_KEY)
    databases = Databases(client)

    for channel in SOURCE_CHANNELS:
        try:
            # Get the latest messages from the source channel
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChatHistory"
            params = {"chat_id": channel, "limit": 10} # Get last 10 messages
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data["ok"]:
                context.log(f"Error getting messages from {channel}: {data['description']}")
                continue

            for message in data["result"]:
                message_id = str(message["message_id"])

                # Check if the message has already been processed
                try:
                    documents = databases.list_documents(
                        database_id=APPWRITE_DATABASE_ID,
                        collection_id=APPWRITE_COLLECTION_ID,
                        queries=[Query.equal("message_id", message_id)]
                    )
                    if documents['total'] > 0:
                        context.log(f"Message {message_id} already processed.")
                        continue
                except Exception as e:
                    context.error(f"Error checking database: {e}")
                    # If we can't check the DB, we shouldn't proceed
                    continue


                if "text" in message:
                    original_text = message["text"]

                    # Modify the text using OpenRouter AI
                    try:
                        ai_response = requests.post(
                            url="https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                                "HTTP-Referer": YOUR_SITE_URL,
                                "X-Title": YOUR_APP_NAME,
                                "Content-Type": "application/json"
                            },
                            data=json.dumps({
                                "model": "mistralai/mistral-7b-instruct:free", # A good free model
                                "messages": [
                                    {"role": "user", "content": f"Rewrite the following message, and at the end, add 'Posted from my awesome channel!': {original_text}"}
                                ]
                            })
                        )
                        ai_response.raise_for_status()
                        modified_text = ai_response.json()["choices"][0]["message"]["content"]
                    except Exception as e:
                        context.error(f"Error with OpenRouter: {e}")
                        # If AI fails, post the original message
                        modified_text = original_text + "\n\nPosted from my awesome channel!"


                    # Post the modified message to your channel
                    try:
                        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                        params = {"chat_id": TELEGRAM_CHAT_ID, "text": modified_text}
                        post_response = requests.get(url, params=params)
                        post_response.raise_for_status()
                        context.log(f"Posted message to {TELEGRAM_CHAT_ID}")

                        # Save the message ID to the database
                        databases.create_document(
                            database_id=APPWRITE_DATABASE_ID,
                            collection_id=APPWRITE_COLLECTION_ID,
                            document_id=ID.unique(),
                            data={"message_id": message_id}
                        )

                    except Exception as e:
                        context.error(f"Error posting to Telegram or saving to DB: {e}")

        except Exception as e:
            context.error(f"An error occurred with channel {channel}: {e}")

    return context.res.json({"status": "ok"})
