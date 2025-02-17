from flask import Flask, request, render_template, jsonify
import pandas as pd

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the Excel data
try:
    df = pd.read_excel("ISO_Tank_Finder.xlsx")  # Exact file name
except FileNotFoundError:
    print("Error: ISO_Tank_Finder.xlsx not found. Ensure it's in the same directory.")
    exit()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cargo_input = request.form.get("cargo")
        contact_details = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone")
        }

        try:
            # Search by UN Number first
            un_number = int(cargo_input)
            tank_type = df.loc[df["UN No."] == un_number, "ISO Tank Type"].iloc[0] # Exact column name
        except (ValueError, KeyError):  # Handles both invalid input and missing column
            try:
                tank_type = df.loc[df["Cargo Name"].str.lower() == cargo_input.lower(), "ISO Tank Type"].iloc[0] # Exact column name, case-insensitive
            except (IndexError, KeyError): # Handles both invalid input and missing column
                tank_type = "Cargo not found in database."

        return jsonify({"tank_type": tank_type, "contact_details": contact_details})

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)  # Set debug=False in production
