from flask import Flask, request, jsonify, redirect
import pandas as pd
from flask_cors import CORS
import requests
import logging
import os
import urllib.parse

app = Flask(__name__)
CORS(app)

# Enable logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load Excel Data
try:
    df = pd.read_excel("ISO_Tank_Finder.xlsx")
    df["Cargo Name"] = df["Cargo Name"].str.strip()
    df["ISO Tank Type"] = df["ISO Tank Type"].str.strip()
    logging.info("Excel file loaded successfully.")
except FileNotFoundError:
    logging.error("Error: ISO_Tank_Finder.xlsx not found.")
    exit()

# OAuth credentials for Zoho Campaigns (Using Environment Variables)
CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET")
REDIRECT_URI = "https://iso-tank-finder.onrender.com/oauth/callback"
ZOHO_ACCOUNTS_URL = "https://accounts.zoho.in/oauth/v2/auth"  # Use .in for India
ZOHO_TOKEN_URL = "https://accounts.zoho.in/oauth/v2/token"  # Use .in for India

# Ensure credentials exist
if not CLIENT_ID or not CLIENT_SECRET:
    logging.error("Missing Zoho OAuth credentials. Set ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET in environment variables.")
    exit()

@app.route("/zoho/oauth")
def zoho_oauth():
    scopes = "ZohoCampaigns.contact.CREATE,ZohoCampaigns.lists.READ"  # Updated scope with uppercase actions
    encoded_scopes = urllib.parse.quote(scopes)  # URL encode the scope

    auth_url = (
        f"{ZOHO_ACCOUNTS_URL}?"
        f"response_type=code&"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={encoded_scopes}"
    )

    logging.info(f"Authorization URL: {auth_url}")
    return redirect(auth_url)

@app.route("/oauth/callback")
def oauth_callback():
    try:
        logging.info(f"Callback request args: {request.args}")  # Log request arguments
        code = request.args.get("code")

        if not code:
            logging.error("Authorization code not found in callback response.")
            return jsonify({"error": "Authorization code not found"}), 400

        logging.info(f"Received Authorization Code: {code}")  # Log auth code

        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }

        logging.info(f"Requesting access token from Zoho...")  # Log before making request
        response = requests.post(ZOHO_TOKEN_URL, data=data)

        logging.info(f"Token response status: {response.status_code}")  # Log response status
        logging.info(f"Token response text: {response.text}")  # Log response text for debugging

        token_data = response.json()

        if "access_token" in token_data:
            logging.info("Zoho OAuth Successful. Access token received.")
            return jsonify({"message": "OAuth successful", "token": token_data})
        else:
            logging.error(f"Failed to retrieve access token: {token_data}")
            return jsonify({"error": "Failed to get access token", "details": token_data}), 400

    except Exception as e:
        logging.exception("OAuth Callback Error")
        return jsonify({"error": "OAuth callback failed", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
