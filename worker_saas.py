import math
import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz

# ==============================================================================
# CONFIGURAÇÕES (Suas chaves estão aqui)
# ==============================================================================
DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
FUSO_BR = pytz.timezone('America/Sao_Paulo')

def calcular_poisson(lambda_val, x):
    if lambda_val <= 0.1: lambda_val = 0.1
    return (math.exp(-lambda_val) * (lambda_val**x)) / math.factorial(x)

def prob_over(lambda_partida, n):
    prob_acumulada = sum(calcular_poisson(lambda_partida, i) for i in range(int(n) + 1))
    return max(0, (1 - prob_acumulada) * 100)

def minerar_futuro():
    print("🦁 MODO FORÇA BRUTA: IGNORANDO FILTROS DE LIGA")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        # Busca jogos de AMANHÃ (Dia 27) para garantir que não pegamos jogos encerrados
        data_teste = (datetime.now(FUSO_BR) + timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"📅 Buscando jogos para: {data_teste}")
        
        res = requests.get(f"https://v3.football.api-sports.io/fixtures?date={data_teste}", headers=headers).json()
        jogos = res.get('response', [])
        
        print(f"   📊 API retornou {len(jogos)} jogos no total.")

        total_salvo = 0
        # Vamos tentar processar os primeiros 30 jogos que aparecerem, independente da liga
        for j in jogos[:30]:
            f_id = j['fixture']['id']
            nome_jogo = f"{j['league']['name']} | {j['teams']['home']['name']} x {j['teams']['away']['name']}"
            
            try:
                # Simula um cálculo de Poisson rápido para teste (para não gastar chamadas de API de predição agora)
                prob_g = round(prob_over(2.5, 2), 2) # Baseado em média 2.5
                prob_c = round(prob_over(10.5, 9), 2) # Baseado em média 10.5

                cur.execute("""
                    INSERT INTO analysis_logs (fixture_id, fixture_name, valor_ev, match_date, gols_ev, cantos_ev, stats_resumo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (fixture_id) 
                    DO UPDATE SET valor_ev = EXCLUDED.valor_ev;
                """, (f_id, nome_jogo, (prob_g+prob_c)/2, j['fixture']['date'], prob_g, prob_c, "Análise Padrão Poisson Ativada"))
                
                conn.commit()
                total_salvo += 1
                print(f"      ✅ SALVO: {nome_jogo}")

            except Exception as e_inner:
                print(f"      ❌ Erro no jogo {f_id}: {e_inner}")
                continue

        conn.close()
        print(f"🏆 SUCESSO! {total_salvo} jogos injetados no seu Dashboard.")
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")

if __name__ == "__main__":
    minerar_futuro()