from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

try:
    df = pd.read_excel("ISO_Tank_Finder.xlsx")
    df["Cargo Name"] = df["Cargo Name"].str.strip()
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
    "T22": ""
}

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

        if tank_type is None:
            message = f"We couldn't determine the best-suited ISO Tank for {cargo_input}. Team BOLT will get back to you soon on the suitable ISO Tank for {cargo_input}."
            response_data = {"tank_type": message, "contact_details": contact_details}
        else:
            tank_type_str = str(tank_type)
            response_data = {"tank_type": tank_type_str, "contact_details": contact_details}
            if tank_type_str in tank_permitted and tank_permitted[tank_type_str]:
                response_data["portable_tank_instructions"] = f"Portable tank instructions also permitted: {tank_permitted[tank_type_str]}"

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
