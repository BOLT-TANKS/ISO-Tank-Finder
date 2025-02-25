from flask import Flask, request, jsonify, redirect
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
import os
import logging

app = Flask(__name__)

# Enable logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load Excel Data (Optional)
try:
    df = pd.read_excel("ISO_Tank_Finder.xlsx")
    df["Cargo Name"] = df["Cargo Name"].str.strip()
    df["ISO Tank Type"] = df["ISO Tank Type"].str.strip()
    logging.info("Excel file loaded successfully.")
except FileNotFoundError:
    logging.error("Error: ISO_Tank_Finder.xlsx not found.")
    df = None  # Set to None if file not found

# Google Sheets API Setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "credentials.json"

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    logging.info("Google Sheets API authentication successful.")
except Exception as e:
    logging.error(f"Google Sheets API Error: {e}")
    creds = None

# Google Sheet Details (Change this to your actual sheet name)
SHEET_NAME = "ISO_Tank_Leads"
try:
    sheet = client.open(SHEET_NAME).sheet1
except Exception as e:
    logging.error(f"Error accessing Google Sheet: {e}")
    sheet = None

# Brevo SMTP Credentials
SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587
SMTP_LOGIN = "vvk.bolt@gmail.com"
SMTP_PASSWORD = os.environ.get("BREVO_SMTP_PASSWORD")  # Store this in environment variables

@app.route("/add_lead", methods=["POST"])
def add_lead():
    """Receive a new lead and store it in Google Sheets."""
    try:
        data = request.json
        name = data.get("name")
        email = data.get("email")
        company = data.get("company")
        cargo = data.get("cargo")

        if not all([name, email, company, cargo]):
            return jsonify({"error": "Missing required fields"}), 400

        # Add data to Google Sheets
        sheet.append_row([name, email, company, cargo])

        # Send Email Notification
        send_email(name, email, company, cargo)

        return jsonify({"message": "Lead added successfully!"}), 200

    except Exception as e:
        logging.error(f"Error adding lead: {e}")
        return jsonify({"error": "Failed to add lead"}), 500

def send_email(name, email, company, cargo):
    """Send an automated email using Brevo SMTP."""
    try:
        subject = "Thank You for Your Inquiry"
        body = f"Hello {name},\n\nThank you for your inquiry regarding {cargo}. Our team will reach out to you soon.\n\nBest Regards,\nBOLT Team"

        message = f"Subject: {subject}\n\n{body}"

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_LOGIN, SMTP_PASSWORD)
            server.sendmail(SMTP_LOGIN, email, message)

        logging.info(f"Email sent to {email}")
    
    except Exception as e:
        logging.error(f"Email sending failed: {e}")

if __name__ == "__main__":
    app.run(debug=True)
