import requests
import os
from datetime import datetime, timedelta

TOKEN = os.getenv("LICHESS_TOKEN")
TEAM_ID = "kidschessclub"  # CHANGE THIS

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

url = "https://lichess.org/api/tournament"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

data = {
    "name": "Wednesday Kids Arena",
    "clockTime": 5,
    "clockIncrement": 0,
    "minutes": 30,
    "startDate": start_timestamp,
    "teamBattleByTeam": TEAM_ID
}

response = requests.post(url, headers=headers, data=data)

print(response.text)
