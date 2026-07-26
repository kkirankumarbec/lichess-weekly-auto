import os
import requests
from datetime import datetime, timedelta

# Read token from GitHub Secret
TOKEN = os.getenv("LICHESS_TOKEN", "").strip()

if not TOKEN:
    raise Exception("LICHESS_TOKEN secret is missing or empty.")

TEAM_ID = "kidschessclub"


def get_next_wednesday():
    now = datetime.utcnow()

    # Wednesday = 2
    target_weekday = 2

    days_ahead = target_weekday - now.weekday()

    if days_ahead <= 0:
        days_ahead += 7

    next_day = now + timedelta(days=days_ahead)

    # Wednesday 8:15 PM IST = 14:45 UTC
    return next_day.replace(
        hour=14,
        minute=45,
        second=0,
        microsecond=0
    )


start_time = get_next_wednesday()

start_timestamp = int(start_time.timestamp() * 1000)

date_string = start_time.strftime("%d %b %Y")

tournament_name = f"Wednesday Kids Arena - {date_string}"

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
    "rated": True,
    "berserkable": False,
    "streakable": False,
    "chatFor": "none",
    "variant": "standard",
    "startDate": start_timestamp,
    "teamBattleByTeam": TEAM_ID
}

print("=" * 60)
print("Creating Tournament")
print("Name :", tournament_name)
print("UTC Start :", start_time)
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
