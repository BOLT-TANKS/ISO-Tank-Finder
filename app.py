from flask import Flask, request, jsonify
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

app = Flask(__name__)

# Google Sheets Authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Cargo Tank Data").sheet1

# Load Cargo Data from Excel
excel_path = "cargo_data.xlsx"
df = pd.read_excel(excel_path)

# Tank Instructions Data
TANK_INSTRUCTIONS = {
    "T11": "T14, T20, T22",
    "T14": "T20, T22",
    "T20": "T22",
    "T22": "No additional instructions"
}

# Function to send email via Brevo
def send_brevo_email(first_name, cargo, tank_type, email):
    brevo_api_url = "https://api.brevo.com/v3/smtp/email"
    brevo_api_key = "YOUR_BREVO_API_KEY"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": brevo_api_key,
    }
    data = {
        "sender": {"name": "BOLT", "email": "noreply@bolt.com"},
        "to": [{"email": email}],
        "subject": "Your Cargo Tank Compatibility Results",
        "htmlContent": f"""
        <p>Dear {first_name},</p>
        <p>Based on your input, the recommended tank type for your cargo ({cargo}) is: <strong>{tank_type}</strong>.</p>
        <p>For more details, please contact us.</p>
        <p>Best Regards,<br>BOLT Team</p>
        """
    }
    response = requests.post(brevo_api_url, json=data, headers=headers)
    return response.status_code

# Function to append data to Google Sheet
def append_to_sheet(data):
    sheet.append_row(data)

# API Endpoint
@app.route("/", methods=["POST"])
def index():
    try:
        data = request.get_json()
        cargo_input = data.get("cargo")
        print(f"Received cargo input: {cargo_input}")

        if not cargo_input:
            return jsonify({"error": "Cargo input is required"}), 400

        contact_details = {
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "email": data.get("email", ""),
            "phone": data.get("phone", ""),
            "location": data.get("location", ""),
        }
        first_name = contact_details["first_name"]
        last_name = contact_details["last_name"]
        email = contact_details["email"]
        phone = contact_details["phone"]
        location = contact_details["location"]

        # Identify tank type
        try:
            un_number = int(cargo_input)
            tank_data = df.loc[df["UN No."].astype(str) == str(un_number), "ISO Tank Type"]
        except ValueError:
            tank_data = df.loc[df["Cargo Name"].str.lower() == cargo_input.lower(), "ISO Tank Type"]

        if not tank_data.empty:
            tank_type = tank_data.iloc[0]
            if pd.isna(tank_type):
                tank_type = "Not Found"
        else:
            tank_type = "Cargo Not Found"

        portable_instructions = None
        if tank_type in TANK_INSTRUCTIONS:
            portable_instructions = "Portable tank instructions also permitted: " + TANK_INSTRUCTIONS[tank_type]

        if tank_type not in ["Cargo Not Found", "Not Found"]:
            send_brevo_email(first_name, cargo_input, tank_type, email)

        response_data = {
            "tank_type": tank_type,
            "contact_details": contact_details
        }
        if portable_instructions:
            response_data["portable_instructions"] = portable_instructions

        # Append all details to the Google Sheet
        append_to_sheet([first_name, last_name, email, phone, location, cargo_input, tank_type])

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
