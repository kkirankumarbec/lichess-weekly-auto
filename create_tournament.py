import requests
import os
from datetime import datetime, timedelta

TOKEN = os.getenv("LICHESS_TOKEN")
TEAM_ID = "kidschessclub"

def get_next_wednesday():
    now = datetime.utcnow()
    target_weekday = 2  # Wednesday

    days_ahead = target_weekday - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7

    next_day = now + timedelta(days=days_ahead)

    # 8:15 PM IST = 14:45 UTC
    return next_day.replace(hour=14, minute=45, second=0, microsecond=0)

start_time = get_next_wednesday()
start_timestamp = int(start_time.timestamp() * 1000)

# ✅ Add formatted date in name
date_string = start_time.strftime("%d %b %Y")
tournament_name = f"Wednesday Kids Arena - {date_string}"

url = "https://lichess.org/api/tournament"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

data = {
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

response = requests.post(url, headers=headers, json=data)

print("Status Code:", response.status_code)
print(response.text)
