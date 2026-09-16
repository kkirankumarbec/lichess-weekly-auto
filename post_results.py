import os
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import requests

TOKEN = os.getenv("LICHESS_TOKEN", "").strip()
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "").strip() or GMAIL_ADDRESS

TEAM_NAME = "KidsChessClub"

LAST_TOURNAMENT_FILE = "last_tournament.json"
RESULTS_LOG_FILE = "results_log.json"
STANDINGS_FILE = "STANDINGS.md"

RESEND = os.getenv("RESEND", "").strip().lower() in ("1", "true", "yes")

PLACE_POINTS = [5, 4, 3, 2, 1]
TOP_N = len(PLACE_POINTS)
_ORDINALS = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th"]


def points_key():
    return ", ".join(f"{_ORDINALS[i]}={p}" for i, p in enumerate(PLACE_POINTS))


def send_email(subject, body):
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD and NOTIFY_EMAIL):
        print("Email not configured - skipping email:", subject)
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = NOTIFY_EMAIL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [NOTIFY_EMAIL], msg.as_string())
    print("Notification email sent to", NOTIFY_EMAIL)


def send_alert(message):
    try:
        send_email(f"[ALERT] lichess-weekly-auto results did not post", message)
    except Exception as exc:
        print("Also failed to send the alert email:", exc)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def fetch_top(tournament_id):
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    resp = requests.get(
        f"https://lichess.org/api/tournament/{tournament_id}/results",
        params={"nb": TOP_N},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    players = []
    for line in resp.text.splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        players.append(
            {
                "rank": row.get("rank"),
                "name": row.get("username", "?"),
                "score": row.get("score", 0),
            }
        )
    players.sort(key=lambda p: p["rank"] if isinstance(p["rank"], int) else 999)
    return players[:TOP_N]


def month_toppers(log, year_month):
    points = {}
    matches = 0
    for entry in log:
        if entry["date"][:7] != year_month:
            continue
        matches += 1
        for player in entry["top"]:
            rank = player["rank"]
            if isinstance(rank, int) and 1 <= rank <= TOP_N and player["name"]:
                points[player["name"]] = points.get(player["name"], 0) + PLACE_POINTS[rank - 1]
    ranked = sorted(points.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    return ranked, matches


def write_standings_md(code, played_dt, top, ranked, month_label, matches):
    lines = [
        f"# {TEAM_NAME} standings",
        "",
        f"_Updated after {code} ({played_dt.strftime('%d %b %Y')})._",
        "",
        f"## {month_label} toppers (after {matches} match(es))",
        "",
        f"Points per match: {points_key()}.",
        "",
        "| # | Player | Points |",
        "|---|--------|--------|",
    ]
    for i, (name, pts) in enumerate(ranked, 1):
        lines.append(f"| {i} | {name} | {pts} |")
    if not ranked:
        lines.append("| - | (no points yet) | 0 |")
    lines += ["", f"### {code} - top {TOP_N}", "", "| Rank | Player |", "|------|--------|"]
    for player in top:
        lines.append(f"| {player['rank']} | {player['name']} |")
    if not top:
        lines.append("| - | (no games played) |")
    with open(STANDINGS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def build_and_send(code, date_str, top, log):
    played_dt = datetime.strptime(date_str, "%Y-%m-%d")
    year_month = date_str[:7]
    month_label = played_dt.strftime("%B %Y")
    ranked, matches = month_toppers(log, year_month)

    month_complete = (played_dt + timedelta(days=7)).month != played_dt.month

    body = [f"{code} - top 5 ({played_dt.strftime('%d %b %Y')})", ""]
    if top:
        for player in top:
            body.append(f"  {player['rank']}. {player['name']}")
    else:
        body.append("  No games were played.")
    body += [
        "",
        f"{month_label} toppers (after {matches} match(es))",
        f"Points legend: {points_key()}",
        "",
    ]
    if ranked:
        for i, (name, pts) in enumerate(ranked, 1):
            body.append(f"  {i}. {name} - {pts} pts")
    else:
        body.append("  (no points yet)")
    body.append("")
    if month_complete and ranked:
        body.append(f"** Player of the Month - {month_label}: {ranked[0][0]} ({ranked[0][1]} pts) **")
        body.append("")
    body.append(f"Full table: {STANDINGS_FILE} in the repo.")

    subject = f"{TEAM_NAME} {code} - top 5 & {month_label} toppers"
    text = "\n".join(body)

    write_standings_md(code, played_dt, top, ranked, month_label, matches)

    print("=" * 60)
    print(text)
    print("=" * 60)
    send_email(subject, text)


def main():
    log = load_json(RESULTS_LOG_FILE, [])

    if RESEND:
        if not log:
            raise SystemExit("No results logged yet - nothing to resend.")
        entry = log[-1]
        build_and_send(entry["code"], entry["date"], entry["top"], log)
        return

    last = load_json(LAST_TOURNAMENT_FILE, None)
    if not last:
        raise SystemExit(
            f"{LAST_TOURNAMENT_FILE} not found - no weekly tournament recorded yet."
        )

    if log and log[-1].get("code") == last["code"]:
        print(f"{last['code']} already has results logged - nothing to do.")
        return

    top = fetch_top(last["id"])
    log.append({"code": last["code"], "date": last["ist_date"], "top": top})
    with open(RESULTS_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

    build_and_send(last["code"], last["ist_date"], top, log)


try:
    main()
except SystemExit as exc:
    send_alert(str(exc))
    raise
except Exception as exc:
    send_alert(f"{type(exc).__name__}: {exc}")
    raise
