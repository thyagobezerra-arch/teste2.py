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

# LISTA EXPANDIDA: Elite + Série B + Estaduais + Ásia + Américas
LIGAS_MONITORADAS = [
    39, 140, 78, 135, 61, 2, 3, 11,   # Elite Europeia
    71, 72, 475, 477, 478, 476, 479,  # Brasil: A, B, Paulista, Carioca, Mineiro, Gaúcho, Paranaense
    188, 283, 292,                    # Ásia: Arábia, Japão, Coreia
    253, 13, 10, 11, 4, 9             # Américas: MLS, Libertadores, Sul-Americana
]

# ==============================================================================
# FUNÇÕES MATEMÁTICAS
# ==============================================================================
def calcular_poisson(lambda_val, x):
    if lambda_val <= 0.1: lambda_val = 0.1
    return (math.exp(-lambda_val) * (lambda_val**x)) / math.factorial(x)

def prob_over(lambda_partida, n):
    prob_acumulada = sum(calcular_poisson(lambda_partida, i) for i in range(int(n) + 1))
    return max(0, (1 - prob_acumulada) * 100)

# ==============================================================================
# MINERADOR GLOBAL
# ==============================================================================
def minerar_futuro():
    print("🦁 MINERADOR EDGE PRO ATIVADO: MODO GLOBAL")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        # Monitora hoje e amanhã para garantir volume
        datas = [datetime.now(FUSO_BR).strftime('%Y-%m-%d'), 
                 (datetime.now(FUSO_BR) + timedelta(days=1)).strftime('%Y-%m-%d')]

        for data_alvo in datas:
            print(f"📅 Varrendo: {data_alvo}")
            res = requests.get(f"https://v3.football.api-sports.io/fixtures?date={data_alvo}", headers=headers).json()
            jogos = res.get('response', [])
            
            # Filtra pelas ligas que queremos
            jogos_filtrados = [j for j in jogos if j['league']['id'] in LIGAS_MONITORADAS]
            print(f"   ✅ Encontrados {len(jogos_filtrados)} jogos nas ligas monitoradas.")

            for j in jogos_filtrados[:20]: # Limite de 20 por dia para não estourar a API
                f_id = j['fixture']['id']
                nome_jogo = f"{j['league']['name']} | {j['teams']['home']['name']} x {j['teams']['away']['name']}"
                
                # Ignora se o jogo já começou ou terminou
                if datetime.fromisoformat(j['fixture']['date'].replace('Z', '+00:00')) < datetime.now(pytz.UTC):
                    continue

                try:
                    p_res = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers).json()
                    if not p_res.get('response'): continue
                    
                    pred = p_res['response'][0]
                    comparison = pred.get('comparison', {})

                    # --- GOLS POISSON ---
                    h_avg = float(pred['teams']['home']['last_5']['goals']['for']['average'] or 1.2)
                    a_avg = float(pred['teams']['away']['last_5']['goals']['for']['average'] or 1.0)
                    prob_gols = round(prob_over(h_avg + a_avg, 2), 2)

                    # --- CANTOS POISSON ---
                    corners_data = comparison.get('corners', {})
                    perc_home = corners_data.get('home', '50%') if corners_info else '50%'
                    if perc_home is None: perc_home = '50%'
                    lambda_c = (float(perc_home.replace('%','')) / 10) * 2
                    prob_cantos = round(prob_over(lambda_c, 9), 2)

                    # --- EV TOTAL ---
                    ev_total = round((prob_gols + prob_cantos) / 2, 2)

                    cur.execute("""
                        INSERT INTO analysis_logs (fixture_id, fixture_name, valor_ev, match_date, gols_ev, cantos_ev, stats_resumo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (fixture_id) DO UPDATE SET 
                            valor_ev = EXCLUDED.valor_ev,
                            gols_ev = EXCLUDED.gols_ev,
                            cantos_ev = EXCLUDED.cantos_ev;
                    """, (f_id, nome_jogo, ev_total, j['fixture']['date'], prob_gols, prob_cantos, "IA: Monitoramento Global Ativo"))
                    conn.commit()
                except:
                    continue

        conn.close()
        print("🏆 FIM! Banco de dados atualizado com a grade global.")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    minerar_futuro()