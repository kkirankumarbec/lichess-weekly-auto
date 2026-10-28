import json
import os
import re
import sys
from datetime import datetime, timezone

import chess
import requests

DIFFICULTY = os.getenv("PUZZLE_DIFFICULTY", "easiest").strip()
ANGLE = os.getenv("PUZZLE_ANGLE", "mix").strip()

PUZZLE_FILE = "docs/puzzle.json"
HISTORY_FILE = "data/puzzle_history.json"


def fetch_puzzle():
    # Called anonymously on purpose: /api/puzzle/next 403s when called with
    # a bearer token that lacks the puzzle:read scope (our LICHESS_TOKEN is
    # scoped for tournament management, not puzzles), and anonymous access
    # is exactly what Lichess's docs describe this endpoint for.
    resp = requests.get(
        "https://lichess.org/api/puzzle/next",
        params={"angle": ANGLE, "difficulty": DIFFICULTY},
    )
    resp.raise_for_status()
    return resp.json()


MOVE_NUMBER_RE = re.compile(r"^\d+\.+$")


def fen_at_ply(pgn_text, ply):
    """Replay the game's SAN moves up to and including `ply` half-moves
    (Lichess's puzzle.pgn is a plain space-separated SAN move list) and
    return the resulting FEN - the position where the solver moves first."""
    tokens = [t for t in pgn_text.split() if not MOVE_NUMBER_RE.match(t)]
    board = chess.Board()
    for san in tokens[: ply + 1]:
        board.push_san(san)
    return board.fen()


def week_key(dt):
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def main():
    data = fetch_puzzle()
    puzzle = data["puzzle"]
    game = data["game"]

    fen = fen_at_ply(game["pgn"], puzzle["initialPly"])
    side_to_move = "white" if fen.split()[1] == "w" else "black"

    now = datetime.now(timezone.utc)
    record = {
        "puzzleId": puzzle["id"],
        "week": week_key(now),
        "pulledAtUtc": now.strftime("%Y-%m-%d %H:%M:%S"),
        "fen": fen,
        "sideToMove": side_to_move,
        # solution[0] is the solver's first move, solution[1] is the
        # opponent's forced reply, and so on.
        "solution": puzzle["solution"],
        "rating": puzzle["rating"],
        "themes": puzzle.get("themes", []),
        "lichessUrl": f"https://lichess.org/training/{puzzle['id']}",
    }

    os.makedirs("docs", exist_ok=True)
    with open(PUZZLE_FILE, "w") as f:
        json.dump(record, f, indent=2)
    print("Wrote", PUZZLE_FILE)
    print(json.dumps(record, indent=2))

    os.makedirs("data", exist_ok=True)
    try:
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    except (FileNotFoundError, ValueError):
        history = []
    history.append(record)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    print("Appended to", HISTORY_FILE)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Failed to pull puzzle: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
