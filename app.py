from flask import Flask, request, jsonify, redirect
import pandas as pd
from flask_cors import CORS
import requests
import logging
import os

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
ZOHO_ACCOUNTS_URL = "https://accounts.zoho.in/oauth/v2/auth" # Use .in for India
ZOHO_TOKEN_URL = "https://accounts.zoho.in/oauth/v2/token" # Use .in for India

@app.route("/zoho/oauth")
def zoho_oauth():
    scopes = "ZohoCampaigns.contact.create,ZohoCampaigns.lists.all" # Start with minimal scopes
    auth_url = (
        f"{ZOHO_ACCOUNTS_URL}?"
        f"response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={scopes}"
    )
    logging.info(f"Authorization URL: {auth_url}")
    return redirect(auth_url)

@app.route("/oauth/callback")
def oauth_callback():
    try:
        logging.info(f"Callback request args: {request.args}") #Log request arguments.
        code = request.args.get("code")
        logging.info(f"Authorization code: {code}") #Log auth code.
        if not code:
            return jsonify({"error": "Authorization code not found"}), 400

        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }

        logging.info(f"Token request data: {data}") #Log the data being sent.
        response = requests.post(ZOHO_TOKEN_URL, data=data)
        logging.info(f"Token response status code: {response.status_code}") #Log response status.
        logging.info(f"Token response text: {response.text}") #Log response text.
        token_data = response.json()
        logging.info(f"Token response json: {token_data}") #Log response json.

        if "access_token" in token_data:
            logging.info("Zoho OAuth Successful")
            return jsonify({"message": "OAuth successful", "token": token_data})
        else:
            logging.error(f"Zoho OAuth Error: {token_data}")
            return jsonify({"error": "Failed to get access token", "details": token_data}), 400

    except Exception as e:
        logging.error(f"OAuth Callback Error: {e}")
        return jsonify({"error": "OAuth callback failed"}), 500

if __name__ == "__main__":
    app.run(debug=True)
