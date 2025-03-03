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

# ... (TANK_INSTRUCTIONS, BREVO_API_KEY, etc. remain the same) ...

def send_brevo_email(name, cargo, tank_type, email):
    # ... (send_brevo_email function remains the same) ...
    pass

def append_to_sheet(data):
    # ... (append_to_sheet function remains the same) ...
    pass

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

        cargo_input = " ".join(cargo_input.split()).strip().lower() #Normalize Spaces and Lower Case.

        try:
            un_number = int(cargo_input)
            tank_data = df.loc[df["UN No."] == un_number, "ISO Tank Type"]

            if not tank_data.empty:
                tank_type = tank_data.iloc[0]
                if pd.isna(tank_type):
                    tank_type = "Not Found"
            else:
                tank_type = "Cargo Not Found"
        except ValueError:
            # Fuzzy matching for cargo name
            cargo_names = df["Cargo Name"].str.lower().tolist()
            best_match, score = process.extractOne(cargo_input, cargo_names)

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
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
