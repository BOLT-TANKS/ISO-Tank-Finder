from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import requests
import numpy as np
import os

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
    # ... your tank_permitted dictionary ...
}

BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"
SENDER_EMAIL = "your_sender_email@example.com"  # Replace with your sender email

def send_brevo_email(to_email, subject, content):
    # ... your send_brevo_email function ...

def append_to_excel(data):
    try:
        new_row = pd.DataFrame([data])
        global df
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel("ISO_Tank_Finder.xlsx", index=False)
        print("Data appended to Excel successfully.")
    except Exception as e:
        print(f"Failed to append data to Excel. Error: {e}")

@app.route("/", methods=["POST"])
def index():
    try:
        data = request.get_json()
        # ... your cargo lookup logic ...

        if tank_type is None or (isinstance(tank_type, float) and np.isnan(tank_type)):
            # ... your "Cargo Not Found" response ...
        else:
            # ... your tank_type response ...

            if contact_details.get("email"):
                # ... your email sending logic ...

            append_to_excel({
                "Cargo": cargo_input,
                "Tank Type": tank_type_str,
                "Name": contact_details.get("name", ""),
                "Email": contact_details.get("email", ""),
                "Phone": contact_details.get("phone", "")
            })

        # ... your FormBold logic ...

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=False) #debug = False for production.
