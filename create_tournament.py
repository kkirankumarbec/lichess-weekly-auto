import os
import requests
from datetime import datetime, timedelta

TOKEN = os.getenv("LICHESS_TOKEN", "").strip()

if not TOKEN:
    raise Exception("LICHESS_TOKEN is missing.")

TEAM_ID = "kidschessclub"


def next_wednesday():
    now = datetime.utcnow()

    days = (2 - now.weekday()) % 7

    if days == 0:
        days = 7

    dt = now + timedelta(days=days)

    # Wednesday 8:15 PM IST
    dt = dt.replace(
        hour=14,
        minute=45,
        second=0,
        microsecond=0
    )

    return dt


start = next_wednesday()

start_ms = int(start.timestamp() * 1000)

name = f"Kids {start.strftime('%d%b')}"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

payload = {
    "name": name,
    "clockTime": 5,
    "clockIncrement": 0,
    "minutes": 30,
    "rated": "true",
    "berserkable": "false",
    "streakable": "false",
    "variant": "standard",
    "chatFor": "none",

    # Wednesday 8:15 PM IST
    "startDate": start_ms,

    # Normal Team Arena
    "team": TEAM_ID
}

print("=" * 60)
print("Creating tournament")
print("Tournament :", name)
print("Starts UTC :", start)
print("=" * 60)

response = requests.post(
    "https://lichess.org/api/tournament",
    headers=headers,
    data=payload
)

print("Status :", response.status_code)
print(response.text)

response.raise_for_status()

data = response.json()

print("=" * 60)

if "id" in data:
    url = f"https://lichess.org/tournament/{data['id']}"
    print("Tournament URL")
    print(url)

print("=" * 60)
print("Tournament Created Successfully")
