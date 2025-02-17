from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Load the Excel file into a DataFrame
df = pd.read_excel('cargo_data.xlsx')

@app.route('/get_iso_tank', methods=['POST'])
def get_iso_tank():
    data = request.json
    cargo_info = data.get('cargo_info', '').strip()

    # Search for the cargo in the DataFrame
    result = df[(df['UN No.'] == cargo_info) | (df['Cargo Name'].str.lower() == cargo_info.lower())]

    if not result.empty:
        iso_tank_type = result.iloc[0]['ISO Tank Type']
        return jsonify({'iso_tank_type': iso_tank_type}), 200
    else:
        return jsonify({'error': 'Cargo not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
