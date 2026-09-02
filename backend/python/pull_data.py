#!/usr/bin/env python3
"""
fantasypros_sync.py
Pull NFL projections from the FantasyPros public v2 API and REPLACE the
contents of the Supabase `public.player` table with them.

This script is destructive by default: it deletes every existing row in
`player` and repopulates the table keyed on FantasyPros player IDs.
Pass --append to add/update rows without wiping the table first.

Setup
-----
    pip install requests supabase python-dotenv

Put these in a .env.local (or .env) next to this script or in any parent
directory - the script walks up looking for one. Real shell env vars win
over the file. Or pass --env-file /explicit/path/.env.local

    FP_API_KEY=your-fantasypros-key
    SUPABASE_URL=https://xxxxxxxx.supabase.co
    SUPABASE_SERVICE_KEY=your-service-role-key

Usage
-----
    # STEP 1 - always run this first on a new season/key. Dumps the raw stat
    # keys FantasyPros actually returns so you can verify STAT_MAP below.
    python fantasypros_sync.py --inspect

    # STEP 2 - build rows and print one, no writes
    python fantasypros_sync.py --dry-run

    # STEP 3 - real syncs (wipes the table, then loads)
    python fantasypros_sync.py                    # week 0 = preseason projections
    python fantasypros_sync.py --week 4           # single-week projections
    python fantasypros_sync.py --ros              # rest-of-season projections
    python fantasypros_sync.py --yes              # skip the delete confirmation
    python fantasypros_sync.py --append           # do not wipe; upsert on top
    python fantasypros_sync.py --with-age         # extra call to fill `age`

Notes
-----
The API docs collapse the projections `stats` object to `[]`, so the exact stat
key names are not documented. STAT_MAP is written with several likely aliases
per column; --inspect prints anything unmapped so you can add it in one place.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import requests

# Paths actually loaded, for the error message if a var is still missing.
LOADED_ENV_FILES: list[Path] = []
ENV_SEARCH_DEPTH = 5


def load_env_files(explicit: str | None = None) -> None:
    """
    Python does not read .env.local automatically - that's a Next.js
    convention, not a language feature. Walk up from this script (and the
    working directory) looking for .env.local / .env and load them.

    Nearest file wins, and anything already exported in the real shell wins
    over all of them (override=False).
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        if explicit:
            sys.exit("--env-file given but python-dotenv isn't installed: "
                     "pip install python-dotenv")
        return

    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            sys.exit(f"env file not found: {path}")
        load_dotenv(path, override=False)
        LOADED_ENV_FILES.append(path)
        return

    bases = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    seen: set[Path] = set()
    for base in bases:
        for directory in [base, *list(base.parents)[:ENV_SEARCH_DEPTH]]:
            for filename in (".env.local", ".env"):
                path = directory / filename
                if path in seen or not path.is_file():
                    continue
                seen.add(path)
                load_dotenv(path, override=False)
                LOADED_ENV_FILES.append(path)


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    if LOADED_ENV_FILES:
        where = "\n".join(f"  - {p}" for p in LOADED_ENV_FILES)
        sys.exit(f"{name} not set.\nLoaded these env files but didn't find it:\n"
                 f"{where}\nCheck the spelling of the key inside them.")
    sys.exit(f"{name} not set, and no .env.local / .env was found.\n"
             f"Either `pip install python-dotenv` and put it next to this "
             f"script or in a parent directory, pass --env-file /path/to/.env.local, "
             f"or export it in your shell.")

BASE_URL = "https://api.fantasypros.com/public/v2/json"
DEFAULT_POSITIONS = ["QB", "RB", "WR", "TE", "K", "DST", "DL", "LB", "DB"]
CHUNK_SIZE = 500
DATA_SRC = "FantasyPros"
INT4_MIN = -2147483648


# --------------------------------------------------------------------------
# Column whitelist - mirrors your DDL exactly. Anything not in here never
# gets sent to Supabase, so a surprise key from FantasyPros can't 400 the
# whole batch.
# --------------------------------------------------------------------------
TABLE_COLUMNS = frozenset("""
id player first_name last_name pos player_position team src_id data_src age exp games
pass_att pass_comp pass_yds pass_yds_g pass_tds pass_int pass_rate
pass_09_tds pass_1019_tds pass_2029_tds pass_3039_tds pass_4049_tds pass_50_tds
pass_250_yds pass_300_yds pass_350_yds sacks
rush_att rush_yds rush_avg rush_tds
rush_09_tds rush_1019_tds rush_2029_tds rush_3039_tds rush_4049_tds rush_50_tds
rush_50_yds rush_100_yds
rec_tgt rec rec_yds rec_yds_g rec_avg rec_tds rec_rz_tgt
rec_09_tds rec_1019_tds rec_2029_tds rec_3039_tds rec_4049_tds rec_50_tds
rec_50_yds rec_100_yds rec_150_yds rec_200_yds
fumbles_lost return_yds scoring_opp site_pts site_fppg
fg fg_att fg_0019 fg_att_0019 fg_2029 fg_att_2029 fg_3039 fg_att_3039
fg_4049 fg_att_4049 fg_4049_att fg_50 fg_att_50 fg_50_att fg_0039 fg_att_39
fg_miss xp xp_att
dst_int dst_fum_rec dst_sacks dst_fumbles dst_tackles
idp_solo idp_asst idp_sacks idp_pd idp_int idp_fum_force idp_fum_rec idp_td
""".split())

# Text columns never get zero-filled.
TEXT_COLUMNS = frozenset({
    "player", "first_name", "last_name", "pos", "player_position",
    "team", "data_src",
})

# Columns your DDL declares as `integer` - these get rounded, everything else
# stays real.
INT_COLUMNS = frozenset({
    "id", "src_id", "age", "exp", "games", "return_yds",
    "fg_4049_att", "fg_50_att", "fg_0039", "fg_att_39",
    "dst_int", "dst_fum_rec", "dst_sacks", "dst_fumbles", "dst_tackles",
})

# Numeric columns that stay NULL when unknown rather than becoming 0.
# `id` and `src_id` are identity, not stats. `age` and `exp` are facts about a
# player, not counts - a 0 there reads as real data and would quietly break any
# filter like `age < 25`. Delete them from this set if you want 0 anyway.
NO_ZERO_FILL = frozenset({"id", "src_id", "age", "exp"})

ZERO_FILL_COLUMNS = frozenset(TABLE_COLUMNS - TEXT_COLUMNS - NO_ZERO_FILL)


# --------------------------------------------------------------------------
# FantasyPros stat key -> your column name.
# Multiple aliases map to the same column on purpose; only one will hit.
# Run --inspect and add any UNMAPPED keys it reports.
# --------------------------------------------------------------------------
STAT_MAP: dict[str, str] = {
    # --- passing ---
    "pass_att": "pass_att", "att": "pass_att", "patt": "pass_att",
    "pass_cmp": "pass_comp", "pass_comp": "pass_comp", "cmp": "pass_comp",
    "pass_yds": "pass_yds", "pyds": "pass_yds",
    "pass_td": "pass_tds", "pass_tds": "pass_tds", "ptd": "pass_tds",
    "pass_int": "pass_int", "pass_ints": "pass_int", "ints": "pass_int",
    "interceptions": "pass_int",
    "pass_rate": "pass_rate", "rating": "pass_rate",
    "sacks": "sacks", "sacked": "sacks",

    # --- rushing ---
    "rush_att": "rush_att", "ratt": "rush_att", "rushing_att": "rush_att",
    "rush_yds": "rush_yds", "ryds": "rush_yds", "rushing_yds": "rush_yds",
    "rush_avg": "rush_avg",
    "rush_td": "rush_tds", "rush_tds": "rush_tds", "rtd": "rush_tds",
    "rushing_tds": "rush_tds",

    # --- receiving ---
    "rec_tgt": "rec_tgt", "targets": "rec_tgt", "tgt": "rec_tgt",
    "rec": "rec", "receptions": "rec",
    "rec_yds": "rec_yds", "receiving_yds": "rec_yds",
    "rec_avg": "rec_avg",
    "rec_td": "rec_tds", "rec_tds": "rec_tds", "receiving_tds": "rec_tds",

    # --- misc offense ---
    "fumbles": "fumbles_lost", "fumbles_lost": "fumbles_lost", "fl": "fumbles_lost",
    "return_yds": "return_yds",
    "games": "games", "g": "games",
    "fpts": "site_pts", "points": "site_pts", "proj_pts": "site_pts",
    "fppg": "site_fppg", "avg": "site_fppg",

    # --- kicking ---
    "fg": "fg", "fgm": "fg",
    "fg_att": "fg_att", "fga": "fg_att",
    "fg_0019": "fg_0019", "fg_2029": "fg_2029", "fg_3039": "fg_3039",
    "fg_4049": "fg_4049", "fg_50": "fg_50",
    "fg_miss": "fg_miss",
    "xp": "xp", "xpt": "xp", "xpm": "xp",
    "xp_att": "xp_att", "xpa": "xp_att",

    # --- team defense ---
    "dst_int": "dst_int", "dst_sacks": "dst_sacks",
    "dst_fum_rec": "dst_fum_rec", "dst_fumbles": "dst_fumbles",
    "dst_tackles": "dst_tackles",

    # --- IDP ---
    "idp_solo": "idp_solo", "solo": "idp_solo", "tackles_solo": "idp_solo",
    "idp_asst": "idp_asst", "assist": "idp_asst", "tackles_ast": "idp_asst",
    "idp_sacks": "idp_sacks",
    "idp_pd": "idp_pd", "pass_def": "idp_pd", "pd": "idp_pd",
    "idp_int": "idp_int",
    "idp_fum_force": "idp_fum_force", "ff": "idp_fum_force",
    "idp_fum_rec": "idp_fum_rec", "fr": "idp_fum_rec",
    "idp_td": "idp_td",
}

NAME_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}
UNMAPPED_KEYS: Counter = Counter()


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
def fp_get(path: str, api_key: str, params: dict | None = None,
           max_retries: int = 4) -> dict:
    """GET against the FantasyPros API with simple backoff on 429/5xx."""
    url = f"{BASE_URL}{path}"
    headers = {"x-api-key": api_key}
    delay = 1.0

    for attempt in range(max_retries):
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
            print(f"  {resp.status_code} on {path} - retrying in {delay:.0f}s",
                  file=sys.stderr)
            time.sleep(delay)
            delay *= 2
            continue
        raise RuntimeError(
            f"FantasyPros {resp.status_code} for {url} "
            f"params={params}: {resp.text[:300]}"
        )
    raise RuntimeError(f"exhausted retries for {url}")


def fetch_projections(api_key: str, season: int, position: str,
                      week: int, ros: bool) -> list[dict]:
    params: dict[str, Any] = {"position": position}
    if ros:
        params["ros"] = "true"
    else:
        params["week"] = week
    payload = fp_get(f"/nfl/{season}/projections", api_key, params)
    return payload.get("players", []) or []


def fetch_ages(api_key: str) -> dict[int, int]:
    """fpid -> age, from the /nfl/players endpoint. One extra request."""
    payload = fp_get("/nfl/players", api_key, {"ecr": "included"})
    ages: dict[int, int] = {}
    for p in payload.get("players", []) or []:
        pid, age = p.get("player_id"), p.get("age")
        if pid is not None and age is not None:
            try:
                ages[int(pid)] = int(age)
            except (TypeError, ValueError):
                pass
    return ages


# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------
def to_num(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value).strip().replace(",", "").replace("%", "")
    if text in ("", "-", "--", "N/A", "null"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def split_name(full: str) -> tuple[str | None, str | None]:
    parts = (full or "").split()
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    if len(parts) > 2 and parts[-1].lower().strip(".") in NAME_SUFFIXES:
        return parts[0], " ".join(parts[1:-1])
    return parts[0], " ".join(parts[1:])


def normalize_stats(raw: Any) -> dict[str, Any]:
    """`stats` may come back as a dict or as a list of dicts. Flatten either."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        flat: dict[str, Any] = {}
        for item in raw:
            if isinstance(item, dict):
                flat.update(item)
        return flat
    return {}


def map_player(p: dict, position: str, ages: dict[int, int] | None) -> dict | None:
    """
    Turn one FantasyPros player object into a sparse `player` row, or None to
    skip. Sparse on purpose - zero-filling happens after dedupe so that a
    later position pull can't overwrite a real value with a 0.
    """
    fpid = p.get("fpid") or p.get("player_id")
    if fpid is None:
        return None
    try:
        row_id = int(fpid)
    except (TypeError, ValueError):
        return None

    name = p.get("name") or p.get("player_name") or ""
    first, last = split_name(name)
    pos = p.get("position_id") or position

    row: dict[str, Any] = {
        "id": row_id,
        "player": name or None,
        "first_name": first,
        "last_name": last,
        "pos": pos,
        "player_position": pos,
        "team": p.get("team_id"),
        "src_id": row_id,
        "data_src": DATA_SRC,
    }

    if ages:
        row["age"] = ages.get(row_id)

    for key, value in normalize_stats(p.get("stats")).items():
        column = STAT_MAP.get(key) or STAT_MAP.get(key.lower())
        if column is None:
            UNMAPPED_KEYS[key] += 1
            continue
        if column not in TABLE_COLUMNS:
            continue
        num = to_num(value)
        if num is None:
            continue
        row[column] = int(round(num)) if column in INT_COLUMNS else num

    # Derived fields your table has but FantasyPros doesn't send directly.
    games = row.get("games")
    if games:
        if "pass_yds" in row and "pass_yds_g" not in row:
            row["pass_yds_g"] = round(row["pass_yds"] / games, 2)
        if "rec_yds" in row and "rec_yds_g" not in row:
            row["rec_yds_g"] = round(row["rec_yds"] / games, 2)
        if "site_pts" in row and "site_fppg" not in row:
            row["site_fppg"] = round(row["site_pts"] / games, 2)
    if row.get("rush_att") and "rush_avg" not in row:
        row["rush_avg"] = round(row.get("rush_yds", 0) / row["rush_att"], 2)
    if row.get("rec") and "rec_avg" not in row:
        row["rec_avg"] = round(row.get("rec_yds", 0) / row["rec"], 2)

    return {k: v for k, v in row.items()
            if k in TABLE_COLUMNS and v is not None}


def dedupe(rows: Iterable[dict]) -> list[dict]:
    """
    Last non-null value wins per id. A player can appear under more than one
    position pull (RB/WR flex eligibility, IDP overlap); this merges rather
    than dropping, and prevents Postgres 'cannot affect row a second time'.
    """
    merged: dict[int, dict] = {}
    for row in rows:
        rid = row["id"]
        if rid in merged:
            merged[rid].update(row)
        else:
            merged[rid] = dict(row)
    return list(merged.values())


def zero_fill(row: dict) -> dict:
    """Every numeric stat column gets an explicit 0 instead of NULL."""
    for column in ZERO_FILL_COLUMNS:
        if row.get(column) is None:
            row[column] = 0
    return row


# --------------------------------------------------------------------------
# Supabase
# --------------------------------------------------------------------------
def get_client():
    from supabase import create_client

    url = require_env("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    if not key:
        require_env("SUPABASE_SERVICE_KEY")
    return create_client(url, key)


def current_row_count(client) -> int:
    resp = client.table("player").select("id", count="exact").limit(1).execute()
    return resp.count or 0


def wipe_table(client) -> None:
    """PostgREST refuses an unfiltered delete, so filter on the full int4 range."""
    client.table("player").delete().gte("id", INT4_MIN).execute()


def upsert_rows(client, rows: list[dict]) -> int:
    written = 0
    for i in range(0, len(rows), CHUNK_SIZE):
        chunk = rows[i:i + CHUNK_SIZE]
        client.table("player").upsert(chunk, on_conflict="id").execute()
        written += len(chunk)
        print(f"  wrote {written}/{len(rows)}")
    return written


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--week", type=int, default=0,
                    help="0 = preseason projections (default)")
    ap.add_argument("--ros", action="store_true",
                    help="rest-of-season projections; overrides --week")
    ap.add_argument("--positions", nargs="+", default=DEFAULT_POSITIONS)
    ap.add_argument("--append", action="store_true",
                    help="do NOT wipe the table first; upsert on top of what's there")
    ap.add_argument("--yes", action="store_true",
                    help="skip the delete confirmation prompt")
    ap.add_argument("--with-age", action="store_true",
                    help="one extra API call to populate `age`")
    ap.add_argument("--inspect", action="store_true",
                    help="print raw stat keys for one player per position, then exit")
    ap.add_argument("--dry-run", action="store_true",
                    help="build rows and print a sample, but do not write")
    ap.add_argument("--env-file", default=None,
                    help="explicit path to a .env.local / .env file")
    args = ap.parse_args()

    load_env_files(args.env_file)
    api_key = require_env("FP_API_KEY")

    replace = not args.append

    if args.inspect:
        for pos in args.positions:
            try:
                players = fetch_projections(api_key, args.season, pos,
                                            args.week, args.ros)
            except RuntimeError as exc:
                print(f"\n=== {pos} === FAILED: {exc}")
                continue
            print(f"\n=== {pos} === ({len(players)} players)")
            if not players:
                continue
            sample = players[0]
            print("  top-level keys:", sorted(sample.keys()))
            stats = normalize_stats(sample.get("stats"))
            for key, value in sorted(stats.items()):
                mapped = STAT_MAP.get(key) or STAT_MAP.get(key.lower())
                flag = f"-> {mapped}" if mapped else "-> UNMAPPED"
                print(f"    {key:<22} = {str(value):<10} {flag}")
        return

    # Fetch everything BEFORE touching the table, so a mid-run API failure
    # never leaves you with an emptied `player`.
    all_rows: list[dict] = []
    ages = fetch_ages(api_key) if args.with_age else None

    for pos in args.positions:
        try:
            players = fetch_projections(api_key, args.season, pos,
                                        args.week, args.ros)
        except RuntimeError as exc:
            print(f"{pos}: skipped - {exc}", file=sys.stderr)
            continue

        rows = [r for r in (map_player(p, pos, ages) for p in players) if r]
        skipped = len(players) - len(rows)
        note = f" ({skipped} skipped, no player id)" if skipped else ""
        print(f"{pos}: {len(rows)} rows{note}")
        all_rows.extend(rows)
        time.sleep(0.3)

    all_rows = [zero_fill(r) for r in dedupe(all_rows)]
    print(f"\nTotal unique rows: {len(all_rows)}")

    if UNMAPPED_KEYS:
        print("\nUNMAPPED stat keys (add these to STAT_MAP):")
        for key, count in UNMAPPED_KEYS.most_common():
            print(f"  {key}  (seen {count}x)")

    if not all_rows:
        print("Nothing to write - leaving the table untouched.")
        return

    if args.dry_run:
        print("\nSample row:")
        for key, value in sorted(all_rows[0].items()):
            print(f"  {key:<18} {value}")
        mode = "REPLACE (wipe then load)" if replace else "APPEND (upsert)"
        print(f"\n--dry-run: nothing written. Mode would be: {mode}")
        return

    client = get_client()

    if replace:
        existing = current_row_count(client)
        print(f"\nREPLACE mode: {existing} existing rows in `player` "
              f"will be deleted and replaced with {len(all_rows)}.")
        if not args.yes:
            if not sys.stdin.isatty():
                sys.exit("Non-interactive shell: pass --yes to confirm the delete.")
            if input("Proceed? [y/N] ").strip().lower() not in ("y", "yes"):
                sys.exit("Aborted - nothing written.")
        wipe_table(client)
        print("  table cleared")

    print()
    upsert_rows(client, all_rows)
    print("Done.")


if __name__ == "__main__":
    main()