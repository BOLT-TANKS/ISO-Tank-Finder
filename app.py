from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import os
import json

app = Flask(__name__)
CORS(app)

# Excel File Configuration
EXCEL_FILE = "ISO_Tank_Finder.xlsx"

# Google Sheets Configuration
SHEET_ID = os.environ.get("SHEET_ID")
CREDENTIALS_FILE = "credentials.json"

# Brevo Configuration
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")

# Retrieve the GitHub secret
credentials_json_string = os.environ.get("GOOGLE_CREDENTIALS_JSON")

# Check if the secret was retrieved successfully
if credentials_json_string:
    try:
        # Parse the JSON string
        credentials_json = json.loads(credentials_json_string)

        # Save the JSON data to a file
        with open("credentials.json", "w") as f:
            json.dump(credentials_json, f)

        print("Credentials file created successfully.")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"Error writing credentials file: {e}")
else:
    print("GOOGLE_CREDENTIALS_JSON secret not found.")

# Initialize Google Sheets client
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
except Exception as e:
    print(f"Error connecting to Google Sheets: {e}")
    exit()

# Load Excel File
try:
    df = pd.read_excel(EXCEL_FILE)
    df["Cargo Name"] = df["Cargo Name"].str.strip()
except FileNotFoundError:
    print(f"Error: {EXCEL_FILE} not found.")
    exit()

def find_tank_type(cargo_input):
    try:
        un_number = int(cargo_input)
        tank_data = df.loc[df["UN No."] == un_number, "ISO Tank Type"]
        if not tank_data.empty:
            return tank_data.iloc[0]
        else:
            tank_data = df.loc[df["Cargo Name"].str.lower() == cargo_input.lower(), "ISO Tank Type"]
            if not tank_data.empty:
                return tank_data.iloc[0]
            else:
                return "Cargo not found in database."
    except ValueError:
        tank_data = df.loc[df["Cargo Name"].str.lower() == cargo_input.lower(), "ISO Tank Type"]
        if not tank_data.empty:
            return tank_data.iloc[0]
        else:
            return "Cargo not found in database."

def send_email(to_email, subject, content):
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
    response = requests.post(BREVO_ENDPOINT, headers=headers, json=payload)
    return response.status_code

@app.route("/", methods=["POST"])
def index():
    try:
        data = request.get_json()
        cargo_input = data.get("cargo")
        first_name = data.get("firstName", "")
        last_name = data.get("lastName", "")
        contact_number = data.get("contactNumber", "")
        email = data.get("email", "")
        location = data.get("location", "")

        if not cargo_input:
            return jsonify({"error": "Cargo input is required"}), 400

        tank_type = find_tank_type(cargo_input)
        contact_details = {
            "firstName": first_name,
            "lastName": last_name,
            "contactNumber": contact_number,
            "email": email,
            "location": location,
            "cargo": cargo_input,
            "tankType": tank_type
        }

        # Send email
        if email:
            subject = "ISO Tank Finder Result"
            content = f"Hello {first_name} {last_name},\n\nYour requested tank type for {cargo_input} is: {tank_type}.\n\nContact Details:\nFirst Name: {first_name}\nLast Name: {last_name}\nContact Number: {contact_number}\nEmail: {email}\nLocation: {location}\nCargo: {cargo_input}\nTank Type: {tank_type}"
            status_code = send_email(email, subject, content)
            if status_code == 201:
                print(f"Email sent successfully to {email}")
            else:
                print(f"Failed to send email to {email}. Status code: {status_code}")

        # Append data to Google Sheet
        try:
            sheet.append_row([first_name, last_name, contact_number, email, location, cargo_input, tank_type])
            print("Data appended to Google Sheet.")
        except Exception as e:
            print(f"Error appending data to Google Sheet: {e}")

        return jsonify({"tank_type": tank_type, "contact_details": contact_details})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
