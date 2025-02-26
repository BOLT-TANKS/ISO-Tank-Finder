from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import requests
import numpy as np
import os

app = Flask(__name__)
CORS(app)

# Load your Excel file (adjust the path if needed)
excel_file_path = "ISO Tank Data.xlsx"  # Replace with your Excel file path
df = pd.read_excel(excel_file_path)

tank_permitted = {
    "T11": "T14",
    "T14": "T50",
    "T50": "T75"
}

BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/templates/send"
SENDER_EMAIL = "info@bolttanks.com"  # Replace with your sender email
BREVO_TEMPLATE_ID = 1  # Using Template ID 1

def send_brevo_template_email(to_email, first_name, cargo_name, tank_type):
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }
    payload = {
        "templateId": BREVO_TEMPLATE_ID,
        "sender": {"name": "ISO Tank Finder", "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "params": {
            "First Name": first_name,
            "Cargo Name": cargo_name,
            "Tank Type": tank_type,
        },
    }
    try:
        response = requests.post(BREVO_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
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
            if contact_details.get("email"):
                first_name = contact_details.get("name", "User")
                send_brevo_template_email(contact_details["email"], first_name, cargo_input, tank_type_str)

        # Send to FormBold
        formbold_url = "https://formbold.com/s/oYkGv"
        try:
            requests.post(formbold_url, json=response_data)
        except Exception as formbold_error:
            print(f"FormBold error: {formbold_error}")

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
