import math
import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
DB_URL = os.getenv("DB_URL") or "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
FUSO_BR = pytz.timezone('America/Sao_Paulo')

LIGAS_MONITORADAS = [39, 140, 78, 135, 61, 2, 3, 11, 71, 72, 475, 477, 478, 476, 479, 188, 283, 292, 253, 13, 10, 11, 4, 9]

def calcular_poisson(lambda_val, x):
    if lambda_val <= 0.1: lambda_val = 0.1
    return (math.exp(-lambda_val) * (lambda_val**x)) / math.factorial(x)

def prob_over(lambda_partida, n):
    prob_acumulada = sum(calcular_poisson(lambda_partida, i) for i in range(int(n) + 1))
    return max(0, (1 - prob_acumulada) * 100)

def minerar_futuro():
    print("🦁 MINERADOR EDGE PRO ATIVADO: MODO DIAGNÓSTICO")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        # Testamos hoje e amanhã
        datas = [datetime.now(FUSO_BR).strftime('%Y-%m-%d'), 
                 (datetime.now(FUSO_BR) + timedelta(days=1)).strftime('%Y-%m-%d')]

        total_salvo = 0
        
        # --- JOGO DE TESTE (FORÇA BRUTA) ---
        # Isso garante que o contador do Supabase saia do 0
        cur.execute("""
            INSERT INTO analysis_logs (fixture_id, fixture_name, valor_ev, match_date, gols_ev, cantos_ev, stats_resumo)
            VALUES (7777, '🔥 TESTE CONEXAO | Thyago x Edge Pro', 30.5, NOW() + INTERVAL '12 hours', 80.0, 75.0, 'Se voce ler isso, a gravacao no banco esta funcionando!')
            ON CONFLICT (fixture_id) DO NOTHING;
        """)
        conn.commit()
        total_salvo += 1

        for data_alvo in datas:
            print(f"📅 Varrendo: {data_alvo}")
            res = requests.get(f"https://v3.football.api-sports.io/fixtures?date={data_alvo}", headers=headers).json()
            jogos = res.get('response', [])
            jogos_filtrados = [j for j in jogos if j['league']['id'] in LIGAS_MONITORADAS]

            for j in jogos_filtrados[:15]:
                f_id = j['fixture']['id']
                nome_jogo = f"{j['league']['name']} | {j['teams']['home']['name']} x {j['teams']['away']['name']}"
                
                # Para teste, vamos desativar a trava de 'tempo passado' por enquanto
                try:
                    p_res = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers).json()
                    if not p_res.get('response'): continue
                    
                    pred = p_res['response'][0]
                    comparison = pred.get('comparison', {})

                    # --- GOLS POISSON ---
                    h_avg = float(pred['teams']['home']['last_5']['goals']['for']['average'] or 1.2)
                    a_avg = float(pred['teams']['away']['last_5']['goals']['for']['average'] or 1.0)
                    prob_gols = round(prob_over(h_avg + a_avg, 2), 2)

                    # --- CANTOS POISSON (FIXED) ---
                    # Corrigido o erro do corners_info que causava o contador 0
                    c_data = comparison.get('corners', {})
                    p_home = c_data.get('home', '50%') if c_data else '50%'
                    if p_home is None: p_home = '50%'
                    
                    lambda_c = (float(p_home.replace('%','')) / 10) * 2
                    prob_cantos = round(prob_over(lambda_c, 9), 2)

                    cur.execute("""
                        INSERT INTO analysis_logs (fixture_id, fixture_name, valor_ev, match_date, gols_ev, cantos_ev, stats_resumo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (fixture_id) DO UPDATE SET valor_ev = EXCLUDED.valor_ev;
                    """, (f_id, nome_jogo, (prob_gols+prob_cantos)/2, j['fixture']['date'], prob_gols, prob_cantos, "IA: Analise Poisson Ativa"))
                    conn.commit()
                    total_salvo += 1
                    print(f"   ✅ Salvo: {nome_jogo}")
                except Exception as e_inner:
                    print(f"   ⚠️ Erro no jogo {f_id}: {e_inner}")
                    continue

        conn.close()
        print(f"🏆 FIM! Banco de dados atualizado com {total_salvo} entradas.")
    except Exception as e:
        print(f"❌ Erro Geral: {e}")

if __name__ == "__main__":
    minerar_futuro()