from supabase import create_client
import os
import pandas as pd
from dotenv import load_dotenv
import heapq
import csv
import io
from .tools.dictionaries import UI_TO_DB, DB_TO_UI

def fetch_all_players(supabase, columns):
    all_rows = []
    page_size = 1000
    start = 0

    while True:
        response = (
            supabase.table("player_new")
            .select(",".join(columns))
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = response.data
        all_rows.extend(batch)

        if len(batch) < page_size:
            break  # last page was partial, so we're done

        start += page_size

    return all_rows


def calculate(user_selected_data, settings, toggles):
    load_dotenv(r"C:\Users\Mattj\Documents\Projects\FantasyFootball\backend\.env.local")

    '''
    {tackles: {selected: true, value: 3}}
    '''
    stats_to_calculate = {}
    stats_to_calculate_query = ["player", "position"]

    # Figure out what stats to query
    for ui_stat, ui_stat_value in user_selected_data.items():
        if ui_stat_value['selected']:
            stats_to_calculate[UI_TO_DB[ui_stat]] = ui_stat_value
            stats_to_calculate_query.append(UI_TO_DB[ui_stat])
        
    # Get the data from supabase
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SECRET_KEY"))
    all_players = fetch_all_players(supabase, stats_to_calculate_query)


    # data=[{'first_name': 'Andy', 'last_name': 'Dalton', 'player_position': 'QB', 'rec': 0, 'rush_3039_tds': 0, 'dst_fumbles': 0, 'idp_fum_force': 0},
    # Go through the response, calculate player score, and find the worst replacement for each position
    
    '''
    position_heaps
    Keeps track of the last replaceable player score at [0]. Accessing that score 
    would look like position_heaps[player_position]["heap"][0]
    '''
    position_heaps = {}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Position", "Overall Score", "Replacement Score"])  # header
    player_attributes = {}
    player_id = 0


    for player in all_players:
        player_score = 0
        player_position = ""
        player_attributes[player_id] = {}
        player_attributes[player_id]["name"] = ''

        # Calculate their score based on the selected stats, key refers to a stat or a column on the player table
        for key, value in player.items(): # Loops through a player row

            user_facing_stat = DB_TO_UI[key] if key in DB_TO_UI else ""

            if key == 'player':
                player_attributes[player_id]["name"] += value
    
            elif key in stats_to_calculate:
                if toggles[user_facing_stat]:
                    player_score += value / float(stats_to_calculate[key]['value'])
                else:
                    player_score += value * float(stats_to_calculate[key]['value']) 
            elif key == 'position':
                player_position = value
                if player_position == 'DST':
                    print('DST')
                player_attributes[player_id]["position"] = player_position

        player_attributes[player_id]["score"] = player_score
            
        # If the position already has a heap, potentially push it, or else create the heap
        try:
            print(settings)
            print(settings['Teams'])
            print(settings['Teams'])

            print(settings[player_position])
            print(settings[player_position])
            players_taken_at_position = int(settings['Teams']) * int(settings[player_position])
            if player_position in position_heaps:
                if position_heaps[player_position]["length"] < players_taken_at_position:
                    heapq.heappush(position_heaps[player_position]["heap"], player_score)
                    position_heaps[player_position]["length"] += 1
                else:
                    if player_score > position_heaps[player_position]["heap"][0]:
                        heapq.heapreplace(position_heaps[player_position]["heap"], player_score)
                
            else:
                position_heaps[player_position] = {"length":0, "heap": []}
                        
        except:
            pass

        player_id += 1

    # Loop through all the players and calculate final scores 

    for player in player_attributes.values():
        
        player_name = player["name"]
        player_position = player["position"]
        player_score = player["score"]
        print(type(position_heaps.get(player_position)))
        if position_heaps.get(player_position).get("heap"):
            score = position_heaps[player_position]["heap"][0]

        writer.writerow([player_name, player_position, player_score, player_score - score])
    print(output.getvalue())
    print(output.getvalue())
    encoded_output = io.BytesIO(output.getvalue().encode('utf-8'))

    return encoded_output


if __name__ == '__main__':

    test_settings = {'Teams': '12', 'QB': '1', 'RB': '2', 'WR':'2', 'TE':'1', 'DB':'1', 'DL':'1', 'LB':'1', 'K':'1', 'DST': '0'}
    test_data = {
        # Offense
        'Passing Yards':        {'selected': True, 'value': '25'},
        'Passing TDs':           {'selected': True, 'value': '6'},
        'Interceptions Thrown':  {'selected': True, 'value': '-1'},
        'Rushing Yards':         {'selected': True, 'value': '10'},
        'Rushing TDs':           {'selected': True, 'value': '6'},
        'Receptions':            {'selected': True, 'value': '0.5'},
        'Receiving Yards':       {'selected': True, 'value': '10'},
        'Receiving TDs':         {'selected': True, 'value': '6'},
        'Fumbles Lost':          {'selected': True, 'value': '-2'},

        # Kickers
        'Extra Points Made':     {'selected': True, 'value': '1'},

        # Defense
        'Tackle Solo':           {'selected': True, 'value': '1'},
        'Tackle Assist':         {'selected': True, 'value': '0.5'},
        'Sack':                  {'selected': True, 'value': '2'},
        'Interception':          {'selected': True, 'value': '3'},
        'Fumble Force':          {'selected': True, 'value': '2'},
        'Fumble Recovery':       {'selected': True, 'value': '2'},
        'Defensive TD':          {'selected': True, 'value': '4'},
        'Pass Defended':         {'selected': True, 'value': '0.5'},
    }

    test_toggles = {
        "Pass Attempts": True,
        "Completions": False,
        "Passing Yards": True,
        "Passing TDs": False,
        "Interceptions Thrown": False,
        "Rush Attempts": False,
        "Rushing Yards": True,
        "Rushing TDs": False,
        "Receptions": False,
        "Receiving Yards": True,
        "Receiving TDs": False,
        "Fumbles Lost": False,
        "Field Goals Made": False,
        "Field Goal Attempts": False,
        "Extra Points Made": False,
        "Team Interceptions": False,
        "Team Fumble Recoveries": False,
        "Team Sacks": False,
        "Team Forced Fumbles": False,
        "Tackle Solo": False,
        "Tackle Assist": False,
        "Sack": False,
        "Pass Defended": False,
        "Interception": False,
        "Fumble Force": False,
        "Fumble Recovery": False,
        "Defensive TD": False
    }
    output = calculate(test_data, test_settings, test_toggles)
    with open("output.csv", 'wb') as f:  # 'wb', not 'w' -- and drop newline='', it's a text-mode-only arg
        f.write(output.getvalue())