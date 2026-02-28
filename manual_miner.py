import requests
from supabase import create_client

# --- SUAS CHAVES (Mantenha as que você já colou antes) ---
SUPABASE_URL = "https://vbxmtclyraxmhvfcnfee.supabase.co"

SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZieG10Y2x5cmF4bWh2ZmNuZmVlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTI5NDUxNCwiZXhwIjoyMDg2ODcwNTE0fQ._scPjsRS5FwYUkIQxiKl5EvWIxyfSw-Qrcgj5uzQtmA"

SPORTMONKS_TOKEN = "T3tAxYr94XOdCLyMNbr5cVbFWjEiJylWMGev1E5m8apwhTV10zjksYboYm5m"


# Conexão
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"❌ Erro ao conectar Supabase: {e}")
    exit()

def buscar_dados_teste():
    print("🚀 Buscando dados de teste no Plano Free...")
    
    # MUDANÇA: Buscando jogos da Liga Dinamarquesa (ID 8) que é liberada no Free
    # Vamos pegar os últimos jogos finalizados para garantir que tenham estatísticas
    url = "https://api.sportmonks.com/v3/football/fixtures"
    
    params = {
        "api_token": SPORTMONKS_TOKEN,
        "filters": "fixtureLeagues:8", # Filtra pela Liga 8 (Danish Superliga)
        "include": "participants;statistics.type;scores", # Pede times, stats e placar
        "per_page": 5, # Pega apenas 5 jogos para teste rápido
        "page": 1
    }

    try:
        response = requests.get(url, params=params)
        dados = response.json()
        
        # Debug: Se der erro, mostra o que veio
        if response.status_code != 200:
            print(f"❌ Erro API: {dados}")
            return

        jogos = dados.get('data', [])
        
        if not jogos:
            print("⚠️ Nenhum jogo encontrado na Liga 8. Tentando buscar SEM filtro de liga...")
            # Tentativa desesperada: Pega qualquer jogo
            del params['filters']
            response = requests.get(url, params=params)
            jogos = response.json().get('data', [])

        if not jogos:
            print("❌ Realmente não conseguimos achar jogos. Verifique seu plano no site.")
            return

        print(f"✅ Encontramos {len(jogos)} jogos! Processando estatísticas...")

        count_salvos = 0
        for jogo in jogos:
            # Pega nomes dos times
            try:
                time_casa = next((p['name'] for p in jogo['participants'] if p['meta']['location'] == 'home'), "Casa")
                time_fora = next((p['name'] for p in jogo['participants'] if p['meta']['location'] == 'away'), "Visitante")
            except:
                time_casa = "Time A"
                time_fora = "Time B"

            # Extrai estatísticas (Se não tiver, coloca 0)
            stats = jogo.get('statistics', [])
            
            def pegar_stat(nome_stat, location):
                # Funçãozinha auxiliar para achar os números no meio do JSON
                for s in stats:
                    if s['type']['name'] == nome_stat and s['location'] == location:
                        return s['data']['value']
                return 0 # Se não achar, retorna 0

            # Monta o pacote para o banco
            match_data = {
                "match_id": str(jogo['id']),
                "match_name": f"{time_casa} x {time_fora}",
                "home_corners": pegar_stat("Corner Kicks", "home"),
                "away_corners": pegar_stat("Corner Kicks", "away"),
                "home_shots_on_goal": pegar_stat("Shots on Goal", "home"),
                "away_shots_on_goal": pegar_stat("Shots on Goal", "away"),
                # Adicione cartões se sua tabela tiver essa coluna
                # "home_cards": pegar_stat("Yellow Cards", "home"), 
            }

            print(f"   📊 {match_data['match_name']} | Escanteios: {match_data['home_corners']} - {match_data['away_corners']}")

            # Salva no Supabase
            try:
                supabase.table("match_stats").upsert(match_data, on_conflict="match_id").execute()
                count_salvos += 1
            except Exception as e:
                print(f"      ⚠️ Erro ao salvar no banco (Verifique se a tabela 'match_stats' existe): {e}")

        print(f"\n🎉 SUCESSO! {count_salvos} jogos com estatísticas inseridos.")
        print("👉 Pode abrir seu Dashboard HTML agora!")

    except Exception as e:
        print(f"❌ Erro fatal: {e}")

if __name__ == "__main__":
    buscar_dados_teste()