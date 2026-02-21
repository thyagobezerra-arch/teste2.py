import requests

API_KEY = "a38db0f256a84b4c71d294ac0e213307"
headers = {'x-rapidapi-key': API_KEY}

def checar_api():
    print("🕵️ Iniciando Diagnóstico...")
    
    # 1. Testar se a chave é válida e ver o limite
    status_url = "https://v3.football.api-sports.io/status"
    res_status = requests.get(status_url, headers=headers).json()
    print(f"📊 Status da Chave: {res_status.get('errors', 'OK')}")
    
    # 2. Buscar QUALQUER jogo que esteja acontecendo agora ou em breve
    # Sem filtro de liga, apenas para ver se a API responde
    print("📡 Buscando jogos gerais (sem filtro)...")
    url = "https://v3.football.api-sports.io/fixtures?next=5"
    res = requests.get(url, headers=headers).json()
    
    jogos = res.get('response', [])
    if jogos:
        print(f"✅ Sucesso! Encontrei {len(jogos)} jogos no sistema.")
        for j in jogos:
            print(f"⚽ {j['teams']['home']['name']} vs {j['teams']['away']['name']} (Liga ID: {j['league']['id']})")
    else:
        print("❌ A API retornou lista vazia mesmo sem filtros.")
        print(f"Resposta completa: {res}")

if __name__ == "__main__":
    checar_api()