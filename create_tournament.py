import os
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

TEAM_ID = "kidschessclub"
COUNTER_FILE = "counter.txt"


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


def next_code():
    try:
        with open(COUNTER_FILE) as f:
            n = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        n = 82
    with open(COUNTER_FILE, "w") as f:
        f.write(str(n + 1))
    return f"KCC{n}"


def send_email(subject, body):
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD and NOTIFY_EMAIL):
        print("Email not configured (GMAIL_ADDRESS / GMAIL_APP_PASSWORD / "
              "NOTIFY_EMAIL missing) - skipping email, tournament still created.")
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = NOTIFY_EMAIL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [NOTIFY_EMAIL], msg.as_string())
    print("Notification email sent to", NOTIFY_EMAIL)


start = next_wednesday()
start_ms = int(start.timestamp() * 1000)
ist_start = start + timedelta(hours=5, minutes=30)

code = next_code()

headers = {"Authorization": f"Bearer {TOKEN}"}

payload = {
    "name": code,
    "clockTime": 5,
    "clockIncrement": 0,
    "minutes": 30,
    "rated": "true",
    "berserkable": "false",
    "streakable": "false",
    "variant": "standard",
    "chatFor": "none",
    "startDate": start_ms,
    # Restrict entry to KidsChessClub team members only
    "team": TEAM_ID,
}

print("=" * 60)
print("Creating tournament")
print("Code       :", code)
print("Starts UTC :", start)
print("Starts IST :", ist_start.strftime("%a %d %b %Y, %I:%M %p"))
print("=" * 60)

response = requests.post(
    "https://lichess.org/api/tournament",
    headers=headers,
    data=payload,
)

print("Status :", response.status_code)
print(response.text)
response.raise_for_status()

data = response.json()
url = f"https://lichess.org/tournament/{data['id']}" if "id" in data else None

print("=" * 60)
if url:
    print("Tournament URL")
    print(url)
print("=" * 60)
print("Tournament Created Successfully")

if url:
    subject = f"♟️ KidsChessClub Tournament {code} — {ist_start.strftime('%a %d %b')}, 8:15 PM IST"
    body = (
        f"Hi,\n\n"
        f"This week's KidsChessClub tournament is ready.\n\n"
        f"Tournament : {code}\n"
        f"Date       : {ist_start.strftime('%A, %d %B %Y')}\n"
        f"Starts     : 8:15 PM IST\n"
        f"Join link  : {url}\n\n"
        f"Only members of the KidsChessClub Lichess team can join.\n"
        f"Share this link in the WhatsApp group so students have time to join before the start.\n\n"
        f"- Sent automatically by lichess-weekly-auto"
    )
    send_email(subject, body)
