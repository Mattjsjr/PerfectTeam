from flask import Flask, jsonify, request, send_file
from position import Player, Position
from flask_cors import CORS
import csv
from python.calculate import calculate
from python.tools.dictionaries import OFFENSE_STATS, DEFENSE_STATS

app = Flask(__name__)
CORS(app)

@app.route("/offense")
def offense():
    RESPONSE = {}
    OFFENSIVE_FIELDS = [field for field in OFFENSE_STATS.keys()]
    RESPONSE["field_entry"] = []
    RESPONSE["stat_button"] = OFFENSIVE_FIELDS
    return jsonify(RESPONSE)

@app.route("/defense")
def defense():

    RESPONSE = {}
    DEFENSIVE_FIELDS = [field for field in DEFENSE_STATS.keys()]
    RESPONSE["field_entry"] = []
    RESPONSE["stat_button"] = DEFENSIVE_FIELDS
    return jsonify(RESPONSE)

@app.route("/settings")
def settings():
    RESPONSE = {}
    FIELD_ENTRY = ["Teams", "QB", "RB", "WR", "TE", "DB", "DL", "LB", "K", "DST"]
    RESPONSE["field_entry"] = FIELD_ENTRY
    RESPONSE["stat_button"] = []
    return jsonify(RESPONSE)

@app.route("/submit", methods=['POST'])
def submit():
    data = request.get_json()

    try:
        selectedStats = data["selectedStats"]
        selectedSettings = data["selectedSettings"]
        selectedToggles = data["selectedToggles"]
        print(selectedStats)
        print(selectedSettings)
        print(selectedToggles)
        csv_output = calculate(selectedStats, selectedSettings, selectedToggles)
        return send_file(
            csv_output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='data.csv'
        )
    except:
        print(f'Some of the required fields: (selectedStats, selectedSettings, or selectedToggles)') 
        return "Some fields are missing", 400

     

if __name__ == "__main__":
    app.run(debug=True, port=5000)