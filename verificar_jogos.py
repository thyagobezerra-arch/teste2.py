import requests
from datetime import datetime, timedelta

API_KEY = "a38db0f256a84b4c71d294ac0e213307"
headers = {'x-rapidapi-key': API_KEY}

# Calcula a data de amanhã
amanha = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

# ID 2 é a Champions League, Season 2025
url = f"https://v3.football.api-sports.io/fixtures?league=2&season=2025&date={amanha}"

print(f"📡 Procurando jogos da Champions para amanhã ({amanha})...")
response = requests.get(url, headers=headers).json()
jogos = response.get('response', [])

if jogos:
    print(f"✅ Encontrados {len(jogos)} jogos:")
    for j in jogos:
        print(f"⚽ {j['teams']['home']['name']} vs {j['teams']['away']['name']}")
else:
    print("⚠️ Não foram encontrados jogos da Champions para amanhã nesta liga/época.")