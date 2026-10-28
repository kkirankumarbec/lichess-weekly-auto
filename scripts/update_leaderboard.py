import csv
import io
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

import requests

LEADERBOARD_FILE = "docs/leaderboard.json"
POINTS_PER_PUZZLE = 1


def load_config():
    with open("config.json") as f:
        return json.load(f)


def fetch_rows(csv_url):
    resp = requests.get(csv_url)
    resp.raise_for_status()
    reader = csv.reader(io.StringIO(resp.text))
    rows = list(reader)
    return rows[1:] if rows else []  # drop header row


def current_week():
    from pull_puzzle import week_key

    return week_key(datetime.now(timezone.utc))


def main():
    config = load_config()
    csv_url = config.get("csv_url", "").strip()
    if not csv_url:
        print("config.json has no csv_url yet - skipping (nothing to tally).")
        return

    rows = fetch_rows(csv_url)

    # One point per (name, week) - a kid can't inflate their score by
    # submitting the same week's puzzle more than once.
    seen = set()
    weekly_points = defaultdict(lambda: defaultdict(int))
    all_time_points = defaultdict(int)
    display_name = {}

    for row in rows:
        if len(row) < 3:
            continue
        _timestamp, raw_name, week = row[0], row[1].strip(), row[2].strip()
        if not raw_name or not week:
            continue
        key = (raw_name.lower(), week)
        if key in seen:
            continue
        seen.add(key)

        display_name.setdefault(raw_name.lower(), raw_name)
        weekly_points[week][raw_name.lower()] += POINTS_PER_PUZZLE
        all_time_points[raw_name.lower()] += POINTS_PER_PUZZLE

    this_week = current_week()
    this_week_board = sorted(
        (
            {"name": display_name[n], "points": p}
            for n, p in weekly_points.get(this_week, {}).items()
        ),
        key=lambda r: (-r["points"], r["name"].lower()),
    )
    all_time_board = sorted(
        (
            {"name": display_name[n], "points": p}
            for n, p in all_time_points.items()
        ),
        key=lambda r: (-r["points"], r["name"].lower()),
    )

    result = {
        "updatedAtUtc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "week": this_week,
        "thisWeek": this_week_board,
        "allTime": all_time_board,
    }

    os.makedirs("docs", exist_ok=True)
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(result, f, indent=2)
    print("Wrote", LEADERBOARD_FILE)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Failed to update leaderboard: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
