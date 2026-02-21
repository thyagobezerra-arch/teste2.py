import requests

API_KEY = "6c0f2aa37b5e66793b0423930e868e42"
URL = "https://v3.football.api-sports.io/fixtures"

headers = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

def buscar_jogos_da_rodada(league_id, season=2025):
    # Parâmetros: Próximos 10 jogos da liga
    querystring = {"league": str(league_id), "season": str(season), "next": "10"}
    
    response = requests.get(URL, headers=headers, params=querystring)
    dados = response.json()

    if not dados.get('response'):
        print("❌ Nenhum jogo encontrado ou erro na chave API.")
        return

    print(f"🏟️ PRÓXIMOS JOGOS ENCONTRADOS:")
    for jogo in dados['response']:
        home = jogo['teams']['home']['name']
        away = jogo['teams']['away']['name']
        data = jogo['fixture']['date']
        match_id = jogo['fixture']['id']
        
        print(f"ID: {match_id} | {home} vs {away} (Data: {data})")

if __name__ == "__main__":
    # ID 39 é a Premier League (Inglaterra)
    # ID 71 é a Série A (Brasil) - Verifique se a temporada já começou
    buscar_jogos_da_rodada(league_id=39)