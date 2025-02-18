from flask import Flask, request, render_template, jsonify
import pandas as pd
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the Excel data
try:
    df = pd.read_excel("ISO_Tank_Finder.xlsx")  # Make sure this file is in the same directory
    df["Cargo Name"] = df["Cargo Name"].str.strip()  # Remove any leading/trailing spaces
except FileNotFoundError:
    print("Error: ISO_Tank_Finder.xlsx not found. Ensure it's in the same directory.")
    exit()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cargo_input = request.form.get("cargo")  # Get cargo input
        print(f"Received cargo input: {cargo_input}")  # Debugging print statement

        # ✅ **CHANGE 1: Check if cargo_input is missing**
        if not cargo_input:
            return jsonify({"error": "Cargo input is required"}), 400

        contact_details = {
            "name": request.form.get("name", ""),
            "email": request.form.get("email", ""),
            "phone": request.form.get("phone", "")
        }

        try:
            # ✅ **CHANGE 2: Convert cargo_input to integer safely**
            un_number = int(cargo_input)
            tank_data = df.loc[df["UN No."] == un_number, "ISO Tank Type"]

            if not tank_data.empty:
                tank_type = tank_data.iloc[0]  # Get first matching row
            else:
                tank_type = "Cargo not found in database."
        except ValueError:
            # ✅ **CHANGE 3: Handle invalid input (non-numeric values)**
            tank_data = df.loc[df["Cargo Name"].str.lower() == cargo_input.lower(), "ISO Tank Type"]

            if not tank_data.empty:
                tank_type = tank_data.iloc[0]
            else:
                tank_type = "Cargo not found in database."

        return jsonify({"tank_type": tank_type, "contact_details": contact_details})

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)  # Set debug=False in production
