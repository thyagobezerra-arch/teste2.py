import math
import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz

# Configurações
DB_URL = os.getenv("DB_URL") or "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
FUSO_BR = pytz.timezone('America/Sao_Paulo')

def calcular_poisson(lambda_val, x):
    if lambda_val <= 0.1: lambda_val = 0.1 # Evita erro matemático
    return (math.exp(-lambda_val) * (lambda_val**x)) / math.factorial(x)

def prob_over(lambda_partida, n):
    prob_acumulada = sum(calcular_poisson(lambda_partida, i) for i in range(int(n) + 1))
    return max(0, (1 - prob_acumulada) * 100)

def minerar_futuro():
    print("🦁 MINERADOR EDGE PRO: BUSCANDO PRÓXIMOS JOGOS")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        # BUSCA HOJE E AMANHÃ (Para sempre ter jogo novo)
        datas = [datetime.now(FUSO_BR).strftime('%Y-%m-%d'), 
                 (datetime.now(FUSO_BR) + timedelta(days=1)).strftime('%Y-%m-%d')]

        for data_alvo in datas:
            print(f"📅 Varrendo: {data_alvo}")
            res = requests.get(f"https://v3.football.api-sports.io/fixtures?date={data_alvo}", headers=headers).json()
            
            for j in res.get('response', [])[:8]: # Analisando os principais de cada dia
                f_id = j['fixture']['id']
                
                # Só processa se o jogo for no FUTURO
                if datetime.fromisoformat(j['fixture']['date'].replace('Z', '+00:00')) < datetime.now(pytz.UTC):
                    continue

                p_res = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers).json()
                if not p_res.get('response'): continue
                
                pred = p_res['response'][0]
                # Médias de Poisson
                h_avg = float(pred['teams']['home']['last_5']['goals']['for']['average'] or 1.2)
                a_avg = float(pred['teams']['away']['last_5']['goals']['for']['average'] or 1.0)
                
                lambda_g = h_avg + a_avg
                prob_gols = round(prob_over(lambda_g, 2), 2)
                
                # Escanteios: Usa a força ofensiva da API para criar o Lambda
                forca_c = float(pred.get('comparison', {}).get('corners', {}).get('home', '50%').replace('%',''))
                prob_cantos = round(prob_over((forca_c/10)*2, 9), 2)

                cur.execute("""
                    INSERT INTO analysis_logs (fixture_id, fixture_name, valor_ev, match_date, gols_ev, cantos_ev, stats_resumo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (fixture_id) DO UPDATE SET valor_ev = EXCLUDED.valor_ev;
                """, (f_id, f"{j['teams']['home']['name']} x {j['teams']['away']['name']}", 
                      (prob_gols+prob_cantos)/2, j['fixture']['date'], prob_gols, prob_cantos, "Análise Poisson Ativa"))
                conn.commit()

        conn.close()
    except Exception as e: print(f"Erro: {e}")

if __name__ == "__main__":
    minerar_futuro()