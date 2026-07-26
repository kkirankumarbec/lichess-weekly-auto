import os
import requests
from datetime import datetime, timedelta

# -----------------------------
# Configuration
# -----------------------------
TOKEN = os.getenv("LICHESS_TOKEN", "").strip()

if not TOKEN:
    raise Exception("LICHESS_TOKEN secret is missing.")

TEAM_ID = "kidschessclub"

# -----------------------------
# Calculate Next Wednesday
# -----------------------------
def get_next_wednesday():
    now = datetime.utcnow()

    target_weekday = 2  # Wednesday

    days_ahead = target_weekday - now.weekday()

    if days_ahead <= 0:
        days_ahead += 7

    next_day = now + timedelta(days=days_ahead)

    # 8:15 PM IST = 14:45 UTC
    return next_day.replace(
        hour=14,
        minute=45,
        second=0,
        microsecond=0
    )


start_time = get_next_wednesday()

start_timestamp = int(start_time.timestamp() * 1000)

# Keep tournament name under 30 chars
date_string = start_time.strftime("%d%b")

tournament_name = f"Kids Arena {date_string}"

# -----------------------------
# API
# -----------------------------
url = "https://lichess.org/api/tournament"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

payload = {
    "name": tournament_name,
    "description": "KidsChessClub Weekly Arena",
    "clockTime": 5,
    "clockIncrement": 0,
    "minutes": 30,
    "rated": "true",
    "berserkable": "false",
    "streakable": "false",
    "chatFor": "none",
    "variant": "standard",
    "startDate": start_timestamp,
    "teamBattleByTeam": TEAM_ID
}

print("=" * 60)
print("Creating Tournament")
print("Tournament :", tournament_name)
print("UTC Start  :", start_time)
print("=" * 60)

response = requests.post(
    url,
    headers=headers,
    data=payload
)

print("Status Code :", response.status_code)
print("Response :")
print(response.text)
print("=" * 60)

response.raise_for_status()

print("Tournament created successfully.")
