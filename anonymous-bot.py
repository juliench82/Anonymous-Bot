from flask import Flask, request, redirect, jsonify
import requests
import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

verifier = SignatureVerifier(SLACK_SIGNING_SECRET)

@app.route('/')
def index():
    return "Hello, Slack Bot!"

@app.route('/slack/oauth/callback', methods=['GET'])
def oauth_callback():
    code = request.args.get('code')
    response = requests.post("https://slack.com/api/oauth.v2.access", data={
        'client_id': SLACK_CLIENT_ID,
        'client_secret': SLACK_CLIENT_SECRET,
        'code': code,
        'redirect_uri': REDIRECT_URI
    })

    if response.status_code != 200:
        return jsonify({"ok": False, "error": "Failed to get access token"}), 400

    auth_response = response.json()
    if not auth_response.get("ok"):
        return jsonify({"ok": False, "error": auth_response.get("error")}), 400

    access_token = auth_response['access_token']
    return jsonify({"ok": True, "access_token": access_token})

@app.route('/post_message', methods=['POST'])
def post_message():
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return jsonify({"ok": False, "error": "Invalid request"}), 400

    data = request.json
    access_token = data.get('access_token')
    channel_id = data.get('channel_id')
    message = data.get('message')

    client = WebClient(token=access_token)

    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=message,
            username='Anonymous'
        )
        return jsonify({"ok": True, "message": "Message posted successfully"}), 200
    except SlackApiError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

if __name__ == '__main__':
    app.run(port=3000)
