import os
import json
import smtplib
from email.mime.text import MIMEText
import requests
from datetime import datetime, timedelta

TOKEN = os.getenv("LICHESS_TOKEN", "").strip()
if not TOKEN:
    raise Exception("LICHESS_TOKEN is missing.")

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "").strip() or GMAIL_ADDRESS

# "weekly"  -> scheduled Wednesday 8:15 PM IST event, code KCC<counter> (KCC82, KCC83, ...)
# "instant" -> starts a few minutes from now, code KCC<day-of-month> (e.g. KCC29)
MODE = os.getenv("MODE", "weekly").strip().lower()
INSTANT_LEAD_MINUTES = 5

TEAM_ID = "kidschessclub"
TEAM_NAME = "KidsChessClub"
COUNTER_FILE = "counter.txt"
COUNTER_START = 82
CONTACT_LINE = "Coach Kirankumar"
# Written after each weekly tournament so the results workflow knows which
# tournament to fetch standings for. Instant tournaments do not touch it.
LAST_TOURNAMENT_FILE = "last_tournament.json"

# Tournament format (kept intentionally standard for the club event).
CLOCK_MINUTES = 5
CLOCK_INCREMENT = 0
DURATION_MINUTES = 30
RATED = True

IST_OFFSET = timedelta(hours=5, minutes=30)


def next_wednesday():
    """Wednesday 14:45 UTC (8:15 PM IST). If run on Wednesday itself before
    that time, targets *today*. Otherwise the coming Wednesday. Never
    returns a time already in the past."""
    now = datetime.utcnow()
    days = (2 - now.weekday()) % 7
    dt = (now + timedelta(days=days)).replace(
        hour=14, minute=45, second=0, microsecond=0
    )
    if dt <= now:
        dt += timedelta(days=7)
    return dt


def load_counter():
    try:
        with open(COUNTER_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return COUNTER_START


def save_counter(n):
    with open(COUNTER_FILE, "w") as f:
        f.write(str(n))


def send_email(subject, body):
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD and NOTIFY_EMAIL):
        print("Email not configured (GMAIL_ADDRESS / GMAIL_APP_PASSWORD / "
              "NOTIFY_EMAIL missing) - skipping email:", subject)
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = NOTIFY_EMAIL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [NOTIFY_EMAIL], msg.as_string())
    print("Notification email sent to", NOTIFY_EMAIL)


def fmt_time(ist_dt):
    return ist_dt.strftime('%I:%M %p').lstrip('0')


def tournament_description(code, ist_start):
    """Plain text shown on the Lichess tournament page itself."""
    return (
        f"Online tournament for the {TEAM_NAME} coaching group.\n\n"
        f"{code} | {ist_start.strftime('%A, %d %B %Y')} | "
        f"{fmt_time(ist_start)} IST | "
        f"{CLOCK_MINUTES}+{CLOCK_INCREMENT} blitz, "
        f"{DURATION_MINUTES}-minute arena, "
        f"{'rated' if RATED else 'casual'}.\n\n"
        f"Only members of the {TEAM_NAME} Lichess team may join, using the "
        f"join code shared in the group.\n\n"
        f"DO: log in as yourself, join on time, play every game, think for "
        f"yourself (no engine, no help), finish your games, and be a good sport.\n\n"
        f"DON'T: share the link or code outside the group, use outside help, "
        f"let anyone else play your moves, stall or deliberately lose, or use "
        f"more than one account.\n\n"
        f"Questions during the event: {CONTACT_LINE}."
    )


def build_email(code, url, ist_start):
    date_str = ist_start.strftime('%d %b %Y')
    short_date = ist_start.strftime('%a %d %b')
    time_str = fmt_time(ist_start)
    subject = f"KidsChessClub Tournament {code} - {short_date}, {time_str} IST"
    body = f"""{code} | {date_str} | {time_str} IST (join a few minutes early)
{CLOCK_MINUTES}+{CLOCK_INCREMENT} Blitz, {DURATION_MINUTES}-min arena, \
{'rated' if RATED else 'casual'} | {TEAM_NAME} team members only
Join code: {code}

Tournament link (tap to open):
{url}

Share the link and code in the WhatsApp group.
"""
    return subject, body


def send_alert(message):
    """Best-effort failure alert - a run that creates nothing should still
    tell the coach, instead of silently skipping the week."""
    try:
        send_email(f"[ALERT] lichess-weekly-auto ({MODE}) did not run", message)
    except Exception as exc:
        print("Also failed to send the alert email:", exc)


def main():
    now = datetime.utcnow()

    if MODE == "instant":
        start = now + timedelta(minutes=INSTANT_LEAD_MINUTES)
        ist_day = (now + IST_OFFSET).day
        code = f"KCC{ist_day}"
        counter_n = None
    else:
        start = next_wednesday()
        counter_n = load_counter()
        code = f"KCC{counter_n}"

    if start <= now + timedelta(minutes=1):
        raise SystemExit(
            f"Computed start {start} UTC is in the past or too soon. Aborting "
            f"so a broken tournament is not created."
        )

    start_ms = int(start.timestamp() * 1000)
    ist_start = start + IST_OFFSET

    headers = {"Authorization": f"Bearer {TOKEN}"}

    payload = {
        "name": code,
        "clockTime": CLOCK_MINUTES,
        "clockIncrement": CLOCK_INCREMENT,
        "minutes": DURATION_MINUTES,
        "rated": "true" if RATED else "false",
        "berserkable": "false",
        "streakable": "false",
        "variant": "standard",
        # Lichess chatFor: 0 = no-one, 10 = team leaders, 20 = team members,
        # 30 = all players. 0 keeps the kids' event chat-free. (The old "none"
        # string was invalid and silently left chat on the default.)
        "chatFor": 0,
        "startDate": start_ms,
        "description": tournament_description(code, ist_start),
        # Restrict entry to KidsChessClub team members only.
        # NOTE: the real Lichess API param is the nested "conditions.teamMember.teamId" -
        # a flat "team" field (used previously) is silently ignored by the API.
        "conditions.teamMember.teamId": TEAM_ID,
        # Real Lichess password gate - players must enter this code to join.
        "password": code,
    }

    print("=" * 60)
    print("Creating tournament")
    print("Mode       :", MODE)
    print("Code       :", code)
    print("Starts UTC :", start)
    print("Starts IST :", ist_start.strftime("%a %d %b %Y, %I:%M %p"))
    print("=" * 60)

    response = requests.post(
        "https://lichess.org/api/tournament",
        headers=headers,
        data=payload,
    )

    if not response.ok:
        print("Lichess API error:", response.status_code)
        print(response.text)
    response.raise_for_status()

    data = response.json()
    url = f"https://lichess.org/tournament/{data['id']}" if "id" in data else None

    # Tournament created successfully - now it is safe to advance the counter.
    if counter_n is not None:
        save_counter(counter_n + 1)
        print("Counter advanced to", counter_n + 1)

    print("=" * 60)
    if url:
        print("Tournament URL")
        print(url)
    print("=" * 60)
    print("Tournament Created Successfully")

    # Record weekly tournaments so the results workflow can look them up.
    if MODE == "weekly" and url:
        with open(LAST_TOURNAMENT_FILE, "w") as f:
            json.dump(
                {
                    "id": data["id"],
                    "code": code,
                    "ist_date": ist_start.strftime("%Y-%m-%d"),
                    "ist_start": ist_start.strftime("%Y-%m-%d %H:%M"),
                },
                f,
                indent=2,
            )
        print("Recorded", LAST_TOURNAMENT_FILE)

    if url:
        subject, body = build_email(code, url, ist_start)
        send_email(subject, body)


try:
    main()
except SystemExit as exc:
    send_alert(str(exc))
    raise
except Exception as exc:
    send_alert(f"{type(exc).__name__}: {exc}")
    raise
