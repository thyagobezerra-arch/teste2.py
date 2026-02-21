import requests
import psycopg2
import time
from datetime import datetime
import os

# --- CONFIGURAÇÃO ---
API_KEY = os.getenv("API_KEY", "a38db0f256a84b4c71d294ac0e213307")
DB_URL = os.getenv("DB_URL", "postgresql://postgres.vbxmtclyraxmhvfcnfee:0LMMYBrja3phgofg@aws-1-sa-east-1.pooler.supabase.com:6543/postgres")

def salvar_no_banco(fixture, tipo, prob, justa, mercado):
    try:
        ev = mercado - justa
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        # Preenche todas as colunas para garantir que apareça em qualquer filtro
        query = """INSERT INTO analysis_logs (fixture_name, mercado_tipo, probabilidade, odd_justa, odd_mercado, valor_ev, prob_over_2_5, fair_odd) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        cur.execute(query, (fixture, tipo, float(prob), float(justa), float(mercado), float(ev), float(prob), float(justa)))
        conn.commit()
        cur.close()
        conn.close()
        print(f"    ✅ {tipo} Salvo: {fixture}")
    except Exception as e: print(f"    ❌ Erro: {e}")

def rodar_minerador_completo():
    headers = {'x-rapidapi-key': API_KEY}
    hoje = datetime.now().strftime('%Y-%m-%d')
    print(f"🚀 Iniciando Varredura Híbrida (Gols + Cantos): {hoje}")
    
    url = f"https://v3.football.api-sports.io/fixtures?date={hoje}"
    response = requests.get(url, headers=headers).json()
    jogos = response.get('response', [])
    
    count = 0
    for jogo in jogos:
        f_id = jogo['fixture']['id']
        nome_jogo = f"{jogo['teams']['home']['name']} vs {jogo['teams']['away']['name']}"

        # BUSCAR ODDS
        url_odds = f"https://v3.football.api-sports.io/odds?fixture={f_id}&bookmaker=8"
        try:
            res_odds = requests.get(url_odds, headers=headers).json()
            bets = res_odds['response'][0]['bookmakers'][0]['bets']
            
            odd_gols = 0.0
            odd_cantos = 0.0

            for b in bets:
                # Mercado de Gols (Over 2.5)
                if b['id'] == 5: 
                    for v in b['values']:
                        if v['value'] == 'Over 2.5': odd_gols = float(v['odd'])
                # Mercado de Escanteios (Over 9.5)
                if "Corners" in b['name']:
                    for v in b['values']:
                        if v['value'] == 'Over 9.5': odd_cantos = float(v['odd'])

            # Se achou Odd de Gols, salva como "Gols"
            if odd_gols > 0:
                prob_gols = 58.0 # Aqui vai sua lógica de Poisson
                justa_gols = round(100/prob_gols, 2)
                salvar_no_banco(nome_jogo, "Gols", prob_gols, justa_gols, odd_gols)

            # Se achou Odd de Cantos, salva como "Escanteios"
            if odd_cantos > 0:
                prob_cantos = 54.0 # Lógica de média de cantos
                justa_cantos = round(100/prob_cantos, 2)
                salvar_no_banco(nome_jogo, "Escanteios (Over 9.5)", prob_cantos, justa_cantos, odd_cantos)

            count += 1
            time.sleep(1)
            if count >= 15: break

        except: continue

if __name__ == "__main__":
    rodar_minerador_completo()