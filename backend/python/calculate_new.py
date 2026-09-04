#!/usr/bin/env python3
"""
calculate_new.py
Same job as calculate.py - turn the league's scoring rules into a CSV of every
player's score - with two differences:

1. The projections come straight from the FantasyPros API instead of the
   Supabase `player` table, so a run is never stale because pull_data.py hasn't
   been run lately. Only the positions the league actually rosters get pulled.
2. Every player is graded against the replacement-level player at their OWN
   position, so the CSV ranks by positional value instead of raw points.

`calculate(user_selected_data, settings, toggles)` keeps the signature and the
return type - a BytesIO of CSV bytes - that app.py's /submit route already
expects, and the first four CSV columns are unchanged, so this is a drop-in
swap for calculate.py.

Value by position
-----------------
`settings` carries the shape of the league: how many teams, and how many
players each team starts at each position. teams x starters is how many players
at that position are locked into starting lineups, so the worst of them is the
replacement level - what you could have had instead. A player's value is their
score minus that baseline, which is why a QB who outscores every RB can still
be worth less than one: the QB you'd settle for is nearly as good, and the RB
you'd settle for is not.

Setup
-----
    pip install requests python-dotenv

Put your key in a .env.local (or .env) next to this script or in any parent
directory - load_env_files() from pull_data.py walks up looking for one. A real
shell env var wins over the file.

    FP_API_KEY=your-fantasypros-key

Usage
-----
    python calculate_new.py                  # preseason projections -> board.csv
    python calculate_new.py --week 4         # single-week projections
    python calculate_new.py --ros            # rest-of-season projections
    python calculate_new.py --out draft.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import sys
import time
from collections import Counter
from typing import Any

import requests

# app.py imports this as a package member (`from python.calculate_new import
# calculate`), but it also runs straight out of this directory, and a relative
# import only works in the first case.
try:
    from .dictionaries import UI_TO_DB
    from .pull_data import (
        DEFAULT_POSITIONS,
        dedupe,
        fetch_projections,
        load_env_files,
        map_player,
        zero_fill,
    )
except ImportError:  # pragma: no cover - depends on how the file is invoked
    from dictionaries import UI_TO_DB
    from pull_data import (
        DEFAULT_POSITIONS,
        dedupe,
        fetch_projections,
        load_env_files,
        map_player,
        zero_fill,
    )


DEFAULT_SEASON = int(os.environ.get("FP_SEASON") or 2026)

# Used only when `settings` doesn't say. Both get a warning on stderr - a
# guessed league size moves every replacement level, so it should be visible.
DEFAULT_TEAMS = 12
IMPLIED_STARTERS = 1

# The settings form has no DST field (see app.py /settings), so a league that
# scores "Team Sacks" would otherwise never pull a defense to score. Any
# position implied by the selected stats but missing from settings is rostered
# at IMPLIED_STARTERS per team.
STAT_PREFIX_POSITIONS = {"dst_": "DST"}

# One /submit is one API pull per position, and a user re-submitting with a
# tweaked weight doesn't need fresh projections. Keyed on what was asked for.
CACHE_TTL_SECONDS = 15 * 60
_PROJECTION_CACHE: dict[tuple, tuple[float, list[dict]]] = {}

CSV_HEADER = [
    # The first four are calculate.py's columns, unchanged, so anything already
    # reading that CSV keeps working. "Replacement Score" is the value over
    # replacement, not the replacement's own score - see "Replacement Baseline".
    "Name",
    "Position",
    "Overall Score",
    "Replacement Score",
    "Team",
    "Replacement Baseline",
    "Position Rank",
    "Overall Rank",
]


# --------------------------------------------------------------------------
# League settings
# --------------------------------------------------------------------------
def setting_value(settings: dict | None, key: str) -> float | None:
    """
    One league setting as a float, or None if it isn't usable.

    The frontend sends {"Teams": {"value": "12"}} (FieldEntry passes a patch);
    calculate.py's test fixtures use the flat {"Teams": "12"}. Accept either.
    """
    raw: Any = (settings or {}).get(key)
    if isinstance(raw, dict):
        raw = raw.get("value")
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def league_size(settings: dict | None) -> int:
    teams = setting_value(settings, "Teams")
    if teams is None or teams < 1:
        print(f"No usable 'Teams' setting - assuming {DEFAULT_TEAMS} teams.",
              file=sys.stderr)
        return DEFAULT_TEAMS
    return int(teams)


def starters_by_position(settings: dict | None, scoring: dict) -> dict[str, int]:
    """
    Position -> starters per team, for every position this league rosters.

    That set is also the set of positions worth pulling from the API: a league
    with no LB slot has no reason to spend a request on linebackers.
    """
    starters: dict[str, int] = {}
    for position in DEFAULT_POSITIONS:
        per_team = setting_value(settings, position)
        if per_team and per_team >= 1:
            starters[position] = int(per_team)

    for prefix, position in STAT_PREFIX_POSITIONS.items():
        if position in starters:
            continue
        if any(column.startswith(prefix) for column in scoring):
            print(f"Scoring {position} stats but settings have no {position} "
                  f"slot - assuming {IMPLIED_STARTERS} per team.", file=sys.stderr)
            starters[position] = IMPLIED_STARTERS

    if not starters:
        print("No positions in the league settings - pulling every position at "
              f"{IMPLIED_STARTERS} starter per team.", file=sys.stderr)
        starters = {position: IMPLIED_STARTERS for position in DEFAULT_POSITIONS}

    return starters


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------
def build_scoring(user_selected_data: dict | None,
                  toggles: dict | None) -> dict[str, tuple[float, bool]]:
    """
    db column -> (weight, divide?), for the stats the user actually turned on.

    A toggle flips a stat to "a point per N of it" - 25 passing yards per point
    rather than 25 points per yard - which is why the weight divides. Stats that
    are unselected, unmapped, or weighted 0 drop out here, so scoring a player
    is a straight walk over the ones that count and can't hit a division by 0.
    """
    scoring: dict[str, tuple[float, bool]] = {}

    for ui_name, entry in (user_selected_data or {}).items():
        if isinstance(entry, dict):
            selected, raw_weight = entry.get("selected"), entry.get("value")
        else:  # a bare weight instead of {"selected": ..., "value": ...}
            selected, raw_weight = True, entry
        if not selected:
            continue

        column = UI_TO_DB.get(ui_name)
        if column is None:
            print(f"Unknown stat '{ui_name}' - skipping it.", file=sys.stderr)
            continue

        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            print(f"Stat '{ui_name}' has a non-numeric weight "
                  f"{raw_weight!r} - skipping it.", file=sys.stderr)
            continue

        if weight == 0:
            continue  # scores nothing multiplied, and blows up divided

        scoring[column] = (weight, bool((toggles or {}).get(ui_name, False)))

    return scoring


def score_player(row: dict, scoring: dict[str, tuple[float, bool]]) -> float:
    total = 0.0
    for column, (weight, divide) in scoring.items():
        value = row.get(column)
        if not value:  # 0 and None both contribute nothing
            continue
        total += value / weight if divide else value * weight
    return total


def player_name(row: dict) -> str:
    first, last = row.get("first_name"), row.get("last_name")
    if first and last:
        return f"{first} {last}"
    return row.get("player") or first or last or "Unknown"


# --------------------------------------------------------------------------
# FantasyPros
# --------------------------------------------------------------------------
def read_api_key(env_file: str | None = None) -> str:
    """
    FP_API_KEY, loading a .env file only if the shell doesn't already have it.

    Raises rather than sys.exit()ing the way pull_data.require_env does - this
    runs inside a Flask request, and killing the process over a missing key
    would take the whole server down with it.
    """
    key = os.environ.get("FP_API_KEY")
    if not key:
        load_env_files(env_file)
        key = os.environ.get("FP_API_KEY")
    if not key:
        raise RuntimeError(
            "FP_API_KEY is not set. Put it in a .env.local / .env next to this "
            "script or in a parent directory, or export it in the shell."
        )
    return key


def fetch_players(api_key: str, positions: list[str], season: int, week: int,
                  ros: bool, use_cache: bool = True) -> list[dict]:
    """
    Every player at the requested positions, as `player`-table-shaped rows.

    Same mapping pull_data.py writes to Supabase - same STAT_MAP, same dedupe
    of players who show up under more than one position, same zero-fill - so a
    row scores identically whether it came from the API or the table.
    """
    cache_key = (season, week, bool(ros), tuple(positions))
    if use_cache:
        cached = _PROJECTION_CACHE.get(cache_key)
        if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
            print(f"Using cached projections ({len(cached[1])} players).")
            return cached[1]

    rows: list[dict] = []
    for position in positions:
        try:
            players = fetch_projections(api_key, season, position, week, ros)
        except (RuntimeError, requests.RequestException) as exc:
            # RuntimeError is a bad status fp_get gave up on; RequestException
            # is the connection never landing. Either way the other positions
            # can still be scored, so note it and keep going.
            print(f"{position}: skipped - {exc}", file=sys.stderr)
            continue
        mapped = [r for r in (map_player(p, position, None) for p in players) if r]
        print(f"{position}: {len(mapped)} players")
        rows.extend(mapped)
        time.sleep(0.3)

    players = [zero_fill(row) for row in dedupe(rows)]
    if not players:
        raise RuntimeError(
            f"FantasyPros returned no players for {', '.join(positions)} "
            f"(season {season}, {'ROS' if ros else f'week {week}'}). Check "
            f"FP_API_KEY and that the season has projections yet."
        )
    if use_cache:
        _PROJECTION_CACHE[cache_key] = (time.time(), players)
    return players


# --------------------------------------------------------------------------
# Replacement level
# --------------------------------------------------------------------------
def replacement_levels(scores_by_position: dict[str, list[float]],
                       starters: dict[str, int], teams: int) -> dict[str, float]:
    """
    Position -> the score of the last starter the league drafts there.

    teams x starters players at a position go into starting lineups, so the
    worst of them is the baseline every other player at that position is worth
    something *over*. A position with fewer projected players than starting
    slots falls back to its worst player; one the league doesn't roster gets 0,
    which leaves those players ranked on raw score.
    """
    levels: dict[str, float] = {}
    for position, scores in scores_by_position.items():
        per_team = starters.get(position)
        if not per_team or not scores:
            levels[position] = 0.0
            continue
        drafted = teams * per_team
        ranked = sorted(scores, reverse=True)
        levels[position] = ranked[min(drafted, len(ranked)) - 1]
    return levels


# --------------------------------------------------------------------------
# The board
# --------------------------------------------------------------------------
def build_board(user_selected_data: dict, settings: dict, toggles: dict,
                season: int = DEFAULT_SEASON, week: int = 0, ros: bool = False,
                positions: list[str] | None = None, api_key: str | None = None,
                use_cache: bool = True) -> list[dict]:
    """
    Every player, scored and valued against their position, best value first.

    Returned as dicts rather than CSV so the same numbers can back a JSON
    endpoint later without going through a spreadsheet.
    """
    scoring = build_scoring(user_selected_data, toggles)
    if not scoring:
        raise ValueError("No usable stats were selected - nothing to score.")

    teams = league_size(settings)
    starters = starters_by_position(settings, scoring)
    if positions is None:
        positions = [p for p in DEFAULT_POSITIONS if p in starters]

    print(f"{teams}-team league, scoring {len(scoring)} stats across "
          f"{', '.join(positions)}")

    board: list[dict] = []
    scores_by_position: dict[str, list[float]] = {}

    for row in fetch_players(api_key or read_api_key(), positions, season,
                             week, ros, use_cache):
        position = row.get("player_position") or row.get("pos") or "UNK"
        score = score_player(row, scoring)
        board.append({
            "name": player_name(row),
            "team": row.get("team") or "",
            "position": position,
            "score": score,
        })
        scores_by_position.setdefault(position, []).append(score)

    levels = replacement_levels(scores_by_position, starters, teams)

    for player in board:
        player["baseline"] = levels.get(player["position"], 0.0)
        player["value"] = player["score"] - player["baseline"]

    # Value order is the draft order, and within one position it's also score
    # order, since every player there shares a baseline.
    board.sort(key=lambda player: player["value"], reverse=True)

    seen_at_position: Counter = Counter()
    for overall_rank, player in enumerate(board, start=1):
        seen_at_position[player["position"]] += 1
        player["overall_rank"] = overall_rank
        player["position_rank"] = seen_at_position[player["position"]]

    return board


def board_to_csv(board: list[dict]) -> io.BytesIO:
    """A built board as CSV bytes, ready for Flask's send_file."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_HEADER)
    for player in board:
        writer.writerow([
            player["name"],
            player["position"],
            round(player["score"], 2),
            round(player["value"], 2),
            player["team"],
            round(player["baseline"], 2),
            player["position_rank"],
            player["overall_rank"],
        ])

    return io.BytesIO(output.getvalue().encode("utf-8"))


def calculate(user_selected_data: dict, settings: dict, toggles: dict,
              season: int = DEFAULT_SEASON, week: int = 0, ros: bool = False,
              positions: list[str] | None = None,
              use_cache: bool = True) -> io.BytesIO:
    """
    The entry point app.py's /submit route calls: settings in, CSV bytes out.
    """
    return board_to_csv(build_board(user_selected_data, settings, toggles,
                                    season=season, week=week, ros=ros,
                                    positions=positions, use_cache=use_cache))


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--season", type=int, default=DEFAULT_SEASON)
    ap.add_argument("--week", type=int, default=0,
                    help="0 = preseason projections (default)")
    ap.add_argument("--ros", action="store_true",
                    help="rest-of-season projections; overrides --week")
    ap.add_argument("--positions", nargs="+", default=None,
                    help="override the positions taken from the settings")
    ap.add_argument("--no-cache", action="store_true",
                    help="always re-pull, even if a recent pull is cached")
    ap.add_argument("--out", default="board.csv")
    ap.add_argument("--top", type=int, default=25,
                    help="how many players to print; 0 for none")
    args = ap.parse_args()

    # Standard PPR-ish scoring with IDP, same fixture calculate.py ships with.
    test_data = {
        # Offense
        'Passing Yards':         {'selected': True, 'value': '25'},
        'Passing TDs':           {'selected': True, 'value': '6'},
        'Interceptions Thrown':  {'selected': True, 'value': '-1'},
        'Rushing Yards':         {'selected': True, 'value': '10'},
        'Rushing TDs':           {'selected': True, 'value': '6'},
        'Receptions':            {'selected': True, 'value': '0.5'},
        'Receiving Yards':       {'selected': True, 'value': '10'},
        'Receiving TDs':         {'selected': True, 'value': '6'},
        'Return Yards':          {'selected': True, 'value': '25'},
        'Fumbles Lost':          {'selected': True, 'value': '-2'},

        # Kickers
        'FG Made 0-19 Yds':      {'selected': True, 'value': '3'},
        'FG Made 20-29 Yds':     {'selected': True, 'value': '3'},
        'FG Made 30-39 Yds':     {'selected': True, 'value': '3'},
        'FG Made 40-49 Yds':     {'selected': True, 'value': '4'},
        'FG Made 50+ Yds':       {'selected': True, 'value': '5'},
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

    # The shape the frontend actually posts. The flat {'Teams': '12'} that
    # calculate.py's fixture uses works too.
    test_settings = {
        'Teams': {'value': '12'},
        'QB': {'value': '1'}, 'RB': {'value': '2'}, 'WR': {'value': '2'},
        'TE': {'value': '1'}, 'DB': {'value': '1'}, 'DL': {'value': '1'},
        'LB': {'value': '1'}, 'K': {'value': '1'},
    }

    # Only the divide-by-weight stats need to be here; everything else defaults
    # to multiplying.
    test_toggles = {
        "Passing Yards": True,
        "Rushing Yards": True,
        "Receiving Yards": True,
        "Return Yards": True,
    }

    board = build_board(test_data, test_settings, test_toggles,
                        season=args.season, week=args.week, ros=args.ros,
                        positions=args.positions, use_cache=not args.no_cache)

    if args.top:
        print(f"\n{'#':>3}  {'Player':<24} {'Pos':<4} {'Team':<4} "
              f"{'Score':>8} {'Value':>8}")
        for player in board[:args.top]:
            print(f"{player['overall_rank']:>3}  {player['name']:<24} "
                  f"{player['position']:<4} {player['team']:<4} "
                  f"{player['score']:>8.2f} {player['value']:>8.2f}")

    with open(args.out, "wb") as f:
        f.write(board_to_csv(board).getvalue())
    print(f"\nWrote {len(board)} players to {args.out}")
