from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS
import requests
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

app = Flask(__name__)
CORS(app)

try:
    df = pd.read_excel("ISO_Tank_Finder.xlsx")
    df["Cargo Name"] = df["Cargo Name"].str.strip()
except FileNotFoundError:
    print("Error: ISO_Tank_Finder.xlsx not found.")
    exit()

TANK_INSTRUCTIONS = {
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
BREVO_TEMPLATE_ID = int(os.environ.get("BREVO_TEMPLATE_ID"))
GOOGLE_CREDENTIALS_GIST_URL = os.environ.get("GOOGLE_CREDENTIALS_GIST_URL")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SHEET_ID = os.environ.get("SHEET_ID")

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

def send_brevo_email(name, cargo, tank_type, email):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BREVO_API_KEY
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    sender = {"name": "BOLT", "email": SENDER_EMAIL}
    to = [{"email": email}]
    params = {"First_Name": name, "Cargo": cargo, "Tank": tank_type}
    template_id = BREVO_TEMPLATE_ID

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, sender=sender, template_id=template_id, params=params)

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print("Email sent successfully!")
        return True
    except ApiException as e:
        print(f"Error sending email: {e}")
        return False

def append_to_sheet(data):
    try:
        response = requests.get(GOOGLE_CREDENTIALS_GIST_URL)
        response.raise_for_status()
        credentials_json = response.json()

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_json, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        sheet.append_row(data)
    except Exception as e:
        print(f"Error appending to sheet: {e}")

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
            "phone": data.get("phone", ""),
            "firstName": data.get("firstName", ""),
            "lastName": data.get("lastName", ""),
            "location": data.get("location", "")
        }
        name = contact_details["name"]
        email = contact_details["email"]
        phone = contact_details["phone"]
        firstName = contact_details["firstName"]
        lastName = contact_details["lastName"]
        location = contact_details["location"]

        if not firstName and not lastName and name:
            name_parts = name.split(" ", 1)
            if len(name_parts) > 0:
                firstName = name_parts[0]
            if len(name_parts) > 1:
                lastName = name_parts[1]

        cargo_input = " ".join(cargo_input.split()).strip().lower() #Added line to normalize spaces

        try:
            un_number = int(cargo_input)
            tank_data = df.loc[df["UN No."] == un_number, "ISO Tank Type"]

            if not tank_data.empty:
                tank_type = tank_data.iloc[0]
                if pd.isna(tank_type):
                    tank_type = "Not Found"
            else: tank_type = "Cargo Not Found"
        except ValueError:
            # Fuzzy matching for cargo name
            cargo_names = df["Cargo Name"].str.lower().tolist()
            best_match, score = process.extractOne(cargo_input, cargo_names)

            print(f"Best match: '{best_match}', Score: {score}")

            if score >= 80:  # Adjust the score threshold as needed
                tank_data = df.loc[df["Cargo Name"].str.lower() == best_match, "ISO Tank Type"]
                if not tank_data.empty:
                    tank_type = tank_data.iloc[0]
                    if pd.isna(tank_type):
                        tank_type = "Not Found"
                else:
                    tank_type = "Cargo Not Found"
            else:
                tank_type = "Cargo Not Found"

        portable_instructions = None
        if tank_type in TANK_INSTRUCTIONS:
            portable_instructions = "Portable tank instructions also permitted: " + TANK_INSTRUCTIONS[tank_type]

        if tank_type != "Cargo Not Found" and tank_type != "Not Found":
            send_brevo_email(name, cargo_input, tank_type, email)

        response_data = {"tank_type": tank_type, "contact_details": contact_details}
        if portable_instructions:
            response_data["portable_instructions"] = portable_instructions

        append_to_sheet([firstName, lastName, email, phone, cargo_input, tank_type, location])

        return jsonify(response_data)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
