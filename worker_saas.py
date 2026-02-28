import math
import requests
import psycopg2
import os
from datetime import datetime
import pytz

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
API_KEY = "a38db0f256a84b4c71d294ac0e213307"

def prob_over_poisson(lambda_val, n):
    """Calcula a probabilidade de sair MAIS de N eventos."""
    if lambda_val <= 0.1: lambda_val = 0.1
    prob_acumulada = sum((math.exp(-lambda_val) * (lambda_val**i)) / math.factorial(i) for i in range(int(n) + 1))
    return max(0, (1 - prob_acumulada) * 100)

def minerar_dia_28():
    print("🦁 MINERADOR ATIVADO: FOCO NO DIA 28/02 (SÁBADO)")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        # DATA ALVO FIXA: Dia 28 de Fevereiro
        data_alvo = "2026-02-28"
        print(f"📅 Buscando grade completa para: {data_alvo}")
        
        url = f"https://v3.football.api-sports.io/fixtures?date={data_alvo}"
        res = requests.get(url, headers=headers).json()
        
        jogos = res.get('response', [])
        print(f"📊 Encontrados {len(jogos)} jogos para o dia 28.")

        total_salvo = 0
        # Vamos processar os primeiros 30 jogos (o limite do plano Free é 100 chamadas/dia)
        for j in jogos[:30]:
            f_id = j['fixture']['id']
            nome_jogo = f"{j['league']['name']} | {j['teams']['home']['name']} x {j['teams']['away']['name']}"
            
            # Cálculo Poisson Estimado (Gols 2.7 e Cantos 10.5)
            prob_g = round(prob_over_poisson(2.7, 2), 2)
            prob_c = round(prob_over_poisson(10.5, 9), 2)
            ev_total = round((prob_g + prob_c) / 4.5, 2) # Ajuste de escala para o velocímetro

            cur.execute("""
                INSERT INTO analysis_logs (fixture_id, fixture_name, valor_ev, match_date, gols_ev, cantos_ev, stats_resumo)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (fixture_id) 
                DO UPDATE SET valor_ev = EXCLUDED.valor_ev;
            """, (f_id, nome_jogo, ev_total, j['fixture']['date'], prob_g, prob_c, "Análise Preditiva de Sábado"))
            
            conn.commit()
            total_salvo += 1
            print(f"   ✅ SALVO: {nome_jogo}")

        conn.close()
        print(f"🏆 SUCESSO! {total_salvo} jogos injetados no banco para amanhã.")
        
    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    minerar_dia_28()