from flask import Flask, jsonify, request, send_file
from position import Player, Position
from flask_cors import CORS
import csv
from python.calculate import calculate

app = Flask(__name__)
CORS(app)

@app.route("/offense")
def offense():
    RESPONSE = {}
    OFFENSE_STATS = [
        "Pass Attempts",
        "Completions",
        "Passing Yards",
        "Passing Yards/Game",
        "Passing TDs",
        "Interceptions Thrown",
        "Passer Rating",
        "Pass TDs 0-9 Yds",
        "Pass TDs 10-19 Yds",
        "Pass TDs 20-29 Yds",
        "Pass TDs 30-39 Yds",
        "Pass TDs 40-49 Yds",
        "Pass TDs 50+ Yds",
        "Games w/ 250+ Pass Yds",
        "Games w/ 300+ Pass Yds",
        "Games w/ 350+ Pass Yds",
        "Sacks Taken",
        "Rush Attempts",
        "Rushing Yards",
        "Yards per Carry",
        "Rushing TDs",
        "Rush TDs 0-9 Yds",
        "Rush TDs 10-19 Yds",
        "Rush TDs 20-29 Yds",
        "Rush TDs 30-39 Yds",
        "Rush TDs 40-49 Yds",
        "Rush TDs 50+ Yds",
        "Games w/ 50+ Rush Yds",
        "Games w/ 100+ Rush Yds",
        "Targets",
        "Receptions",
        "Receiving Yards",
        "Receiving Yards/Game",
        "Yards per Reception",
        "Receiving TDs",
        "Red Zone Targets",
        "Rec TDs 0-9 Yds",
        "Rec TDs 10-19 Yds",
        "Rec TDs 20-29 Yds",
        "Rec TDs 30-39 Yds",
        "Rec TDs 40-49 Yds",
        "Rec TDs 50+ Yds",
        "Games w/ 50+ Rec Yds",
        "Games w/ 100+ Rec Yds",
        "Games w/ 150+ Rec Yds",
        "Games w/ 200+ Rec Yds",
        "Fumbles Lost",
        "Return Yards",
        "Field Goals Made",
        "Field Goal Attempts",
        "FG Made 0-19 Yds",
        "FG Attempts 0-19 Yds",
        "FG Made 20-29 Yds",
        "FG Attempts 20-29 Yds",
        "FG Made 30-39 Yds",
        "FG Attempts 30-39 Yds",
        "FG Made 40-49 Yds",
        "FG Attempts 40-49 Yds",
        "FG Made 50+ Yds",
        "FG Attempts 50+ Yds",
        "FG Attempts 40-49 (Count)",
        "FG Attempts 50+ (Count)",
        "FG Made 0-39 Yds",
        "FG Attempts 0-39 Yds",
        "Field Goals Missed",
        "Extra Points Made",
        "Extra Point Attempts",
    ]

    RESPONSE["field_entry"] = []
    RESPONSE["stat_button"] = OFFENSE_STATS
    return jsonify(RESPONSE)

@app.route("/defense")
def defense():

    RESPONSE = {}
    DEFENSE_STATS = [
        "Team Interceptions",
        "Team Fumble Recoveries",
        "Team Sacks",
        "Team Forced Fumbles",
        "Team Tackles",
        "Tackle Solo",
        "Tackle Assist",
        "Sack",
        "Pass Defended",
        "Interception",
        "Fumble Force",
        "Fumble Recovery",
        "Defensive TD",
    ]
    RESPONSE["field_entry"] = []
    RESPONSE["stat_button"] = DEFENSE_STATS
    return jsonify(RESPONSE)

@app.route("/settings")
def settings():
    RESPONSE = {}
    FIELD_ENTRY = ["Teams", "QB", "RB", "WR", "TE", "DB", "DL", "LB", "K"]
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