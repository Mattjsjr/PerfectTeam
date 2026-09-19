import pytest
from calculate import *

# =============== build_query =================

build_query_input_1 = "a"
build_query_input_2 = 1
def test_build_query_rejects_non_player():
    with pytest.raises(TypeError, match=f"build_query only accepts a a JSON object containing player information. Received {build_query_input_1} instead."):
        build_query(build_query_input_1)
        build_query(build_query_input_2)

testbuild_query_rejects_invalid_dictionary_1 = {}
def testbuild_query_rejects_invalid_dictionary():
    with pytest.raises(ValueError, match=f"malformed entry for '{testbuild_query_rejects_invalid_dictionary_1}': expected a dictionary with 'selected' key"):
        build_query(testbuild_query_rejects_invalid_dictionary_1)

# =============== validate_toggles_stats =================

stats_not_mapped_in_db = {
    'Statistics':        {'selected': True, 'value': '25'},
}

toggles = {
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

def test_validate_toggles_stats_invalid_stat_name():
    with pytest.raises(ValueError):
        validate_toggles_stats(toggles, stats_not_mapped_in_db)

stats_value_not_number = {
    'Passing Yards':        {'selected': True, 'value': 'abc'},
}

def test_validate_toggles_stats_stat_not_number():
    with pytest.raises(ValueError):
        validate_toggles_stats(toggles, stats_value_not_number)

stats_value_is_zero = {
    'Passing Yards':        {'selected': True, 'value': 'abc'},
}

def test_validate_toggles_stats_value_is_zero():
    with pytest.raises(ValueError):
        validate_toggles_stats(toggles, stats_value_is_zero)
