from flask import Flask, request, jsonify, redirect
import pandas as pd
from flask_cors import CORS
import requests
import numpy as np
import logging

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

# OAuth credentials for Zoho
CLIENT_ID = "1000.83BH88U2AT9NPAO0T8KSB4PP7347TT"
CLIENT_SECRET = "aa75e24d3f2171f268b04fa00110a7f1cefa860fbe"
REDIRECT_URI = "https://iso-tank-finder.onrender.com/oauth/callback"

@app.route("/zoho/oauth")
def zoho_oauth():
    auth_url = (
        "https://accounts.zoho.com/oauth/v2/auth?"
        f"response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=ZohoCRM.modules.ALL"
    )
    return redirect(auth_url)

@app.route("/oauth/callback")
def oauth_callback():
    try:
        code = request.args.get("code")
        if not code:
            return jsonify({"error": "Authorization code not found"}), 400

        token_url = "https://accounts.zoho.com/oauth/v2/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }

        response = requests.post(token_url, data=data)
        token_data = response.json()

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
