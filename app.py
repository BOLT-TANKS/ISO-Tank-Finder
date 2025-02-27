from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import requests
import numpy as np
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
CORS(app)

try:
    df = pd.read_excel("ISO_Tank_Finder.xlsx")
    df["Cargo Name"] = df["Cargo Name"].str.strip()
    df["ISO Tank Type"] = df["ISO Tank Type"].str.strip()
except FileNotFoundError:
    print("Error: ISO_Tank_Finder.xlsx not found.")
    exit()

tank_permitted = {
    "T1": "T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22",
    "T2": "T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22",
    "T3": "T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22",
    "T4": "T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22",
    "T5": "T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22",
    "T6": "T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22",
    "T7": "T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22",
    "T8": "T9, T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22",
    "T9": "T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22",
    "T10": "T11, T19, T20, T21, T22",
    "T12": "T14, T16, T18, T19, T20, T21, T22",
    "T13": "T19, T20, T21, T22",
    "T15": "T16, T17, T18, T19, T20, T21, T22",
    "T16": "T17, T18, T19, T20, T21, T22",
    "T17": "T18, T19, T20, T21, T22",
    "T18": "T19, T20, T21, T22",
    "T19": "T20, T22",
    "T20": "T22",
    "T21": "T22",
}

BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"
SENDER_EMAIL = "info@bolttanks.com"

# Google Sheets Configuration
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "your-service-account-credentials.json"
SPREADSHEET_ID = "1geFLxGjdEUUj2Ua9VDhDlQeDLDg-ZNuErz7KId-8_yY"
WORKSHEET_NAME = "Sheet1"

def send_brevo_email(to_email, subject, content):
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }
    payload = {
        "sender": {"name": "ISO Tank Finder", "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": content,
    }
    try:
        response = requests.post(BREVO_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Email sent successfully to {to_email}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send email to {to_email}. Error: {e}")

def append_to_excel(data):
    try:
        new_row = pd.DataFrame([data])
        global df
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel("ISO_Tank_Finder.xlsx", index=False)
        print("Data appended to Excel successfully.")
    except Exception as e:
        print(f"Failed to append data to Excel. Error: {e}")

def append_to_google_sheet(data):
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        row = [data.get("Cargo", ""), data.get("Tank Type", ""), data.get("Name", ""), data.get("Email", ""), data.get("Phone", "")]
        sheet.append_row(row)
        print("Data appended to Google Sheet successfully.")
    except Exception as e:
        print(f"Failed to append data to Google Sheet. Error: {e}")

@app.route("/", methods=["POST"])
def index():
    try:
        data = request.get_json()
        cargo_input = data.get("cargo")
        print(f"Received cargo input: {cargo_input}")

        if not cargo_input:
            return jsonify({"error": "Cargo input is required"}), 400

        contact_details = {
            "name": data.get("name", ""),
            "email": data.get("email", ""),
            "phone": data.get("phone", "")
        }

        try:
            un_number = int(cargo_input)
            tank_data = df.loc[df["UN No."] == un_number, "ISO Tank Type"]

            if not tank_data.empty:
                tank_type = tank_data.iloc[0]
            else:
                tank_type = None
        except ValueError:
            tank_data = df.loc[df["Cargo Name"].str.lower() == cargo_input.lower(), "ISO Tank Type"]

            if not tank_data.empty:
                tank_type = tank_data.iloc[0]
            else:
                tank_type = None

        if tank_type is None or (isinstance(tank_type, float) and np.isnan(tank_type)):
            response_data = {"tank_type": "Cargo Not Found", "contact_details": contact_details}
        else:
            tank_type_str = str(tank_type)
            print(f"Tank Type: {tank_type_str}")
            response_data
