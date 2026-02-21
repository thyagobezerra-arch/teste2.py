import requests
import psycopg2
from scipy.stats import poisson
import time

API_KEY = "a38db0f256a84b4c71d294ac0e213307" 
DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:0LMMYBrja3phgofg@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

def salvar_no_banco(fixture_name, prob, fair_odd):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO analysis_logs (fixture_name, prob_over_2_5, fair_odd) VALUES (%s, %s, %s)", (fixture_name, prob, fair_odd))
        conn.commit()
        conn.close()
        print(f"    ✅ Salvo: {fixture_name}")
    except Exception as e:
        print(f"    ❌ Erro: {e}")

def rodar_global():
    print("🌍 Buscando os próximos 10 jogos de QUALQUER liga no mundo...")
    headers = {'x-rapidapi-key': API_KEY}
    
    # Busca global: sem filtro de liga ou data, apenas os próximos 10
    url = "https://v3.football.api-sports.io/fixtures?next=10"
    
    response = requests.get(url, headers=headers).json()
    jogos = response.get('response', [])

    if not jogos:
        print("❌ A API não retornou nada. Verifique sua chave ou limite de créditos.")
        return

    for jogo in jogos:
        home = jogo['teams']['home']['name']
        away = jogo['teams']['away']['name']
        liga_nome = jogo['league']['name']
        
        # Como é uma busca global, vamos usar uma média padrão para o teste
        prob_over = 62.5  # Valor de teste
        odd_justa = 1.60
        
        print(f"⚽ {home} vs {away} ({liga_nome})")
        salvar_no_banco(f"[{liga_nome}] {home} vs {away}", prob_over, odd_justa)
        time.sleep(0.5)

if __name__ == "__main__":
    rodar_global()