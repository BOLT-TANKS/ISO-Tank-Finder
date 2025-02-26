from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import requests
import numpy as np
import os #Add this import

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

BREVO_API_KEY = os.environ.get("BREVO_API_KEY") # Get API Key from Environment Variables.
BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"
SENDER_EMAIL = "your_sender_email@example.com" #Replace with your sender email

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
        response.raise_for_status() #Raise error for bad status codes.
        print(f"Email sent successfully to {to_email}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send email to {to_email}. Error: {e}")

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
            response_data = {"tank_type": tank_type_str, "contact_details": contact_details}

            if tank_type_str in tank_permitted:
                response_data["portable_tank_instructions"] = f"Tank Type also permitted: {tank_permitted[tank_type_str]}"
            if contact_details.get("email"): #Send email if email is provided.
                subject = "ISO Tank Finder Result"
                content = f"Tank Type: {tank_type_str}\nPortable Tank Instructions: {tank_permitted.get(tank_type_str, 'None')}"
                send_brevo_email(contact_details["email"], subject, content)

        # Send to FormBold
        formbold_url = "https://formbold.com/s/oYkGv"
        try:
            requests.post(formbold_url, json=response_data)
        except Exception as formbold_error:
            print(f"
