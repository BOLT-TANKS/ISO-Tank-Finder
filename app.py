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

# Change the region URL based on your Zoho Account (India, Global, EU)
ZOHO_REGION = "in"  # Change to "com" (US) or "eu" (Europe) if needed
ZOHO_ACCOUNTS_URL = f"https://accounts.zoho.{ZOHO_REGION}/oauth/v2/auth"
ZOHO_TOKEN_URL = f"https://accounts.zoho.{ZOHO_REGION}/oauth/v2/token"

@app.route("/zoho/oauth")
def zoho_oauth():
    # Correct OAuth Scopes
    scopes = "ZohoCampaigns.contact.ALL,ZohoCampaigns.lists.READ"
    encoded_scopes = urllib.parse.quote(scopes)  # Ensure URL encoding
    
    auth_url = (
        f"{ZOHO_ACCOUNTS_URL}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={encoded_scopes}"
        f"&access_type=offline"  # Ensure refresh token is granted
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

        # Exchange auth code for access token
        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }

        logging.info(f"Token request data: {data}")  # Log token request data
        response = requests.post(ZOHO_TOKEN_URL, data=data)
        token_data = response.json()

        logging.info(f"Token response: {token_data}")  # Log response

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
