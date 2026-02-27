import math
import requests
import psycopg2
import os
from datetime import datetime
import pytz
from telegram_bot import enviar_alerta, criar_mensagem_vip

# ==============================================================================
# CONFIGURAÇÕES (Mantenha suas chaves originais)
# ==============================================================================
DB_URL = os.getenv("DB_URL") or "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
FUSO_BR = pytz.timezone('America/Sao_Paulo')
LIGAS_ELITE = [39, 140, 78, 135, 61, 71, 2, 13, 11, 4, 9, 3] # Principais ligas mundiais

# ==============================================================================
# CÉREBRO MATEMÁTICO (POISSON)
# ==============================================================================
def calcular_poisson(lambda_val, x):
    """Calcula a probabilidade de um evento ocorrer exatamente X vezes."""
    if lambda_val <= 0: return 0
    return (math.exp(-lambda_val) * (lambda_val**x)) / math.factorial(x)

def probabilidade_over_n(lambda_partida, n):
    """Calcula a probabilidade de ocorrer MAIS de N eventos."""
    prob_acumulada = 0
    for i in range(int(n) + 1):
        prob_acumulada += calcular_poisson(lambda_partida, i)
    return max(0, (1 - prob_acumulada) * 100)

# ==============================================================================
# MINERADOR PRINCIPAL
# ==============================================================================
def minerar_futuro():
    print("🚀 INICIANDO MINERADOR PROFISSIONAL (POISSON BLINDADO)")
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Garante que a estrutura do banco está pronta para os novos mercados
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_logs (
                id SERIAL PRIMARY KEY, 
                fixture_id INTEGER UNIQUE,
                fixture_name TEXT, 
                valor_ev FLOAT, 
                match_date TIMESTAMP, 
                gols_ev FLOAT DEFAULT 0,
                cantos_ev FLOAT DEFAULT 0,
                chutes_ev FLOAT DEFAULT 0,
                cartoes_ev FLOAT DEFAULT 0,
                stats_resumo TEXT, 
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()

        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        data_hoje = datetime.now(FUSO_BR).strftime('%Y-%m-%d')
        
        # Busca jogos de hoje
        url_fixtures = f"https://v3.football.api-sports.io/fixtures?date={data_hoje}"
        res_api = requests.get(url_fixtures, headers=headers, timeout=20).json()
        jogos = res_api.get('response', [])

        total_processado = 0
        if jogos:
            # Filtra apenas ligas de elite para economizar chamadas de API
            lista_final = [j for j in jogos if j['league']['id'] in LIGAS_ELITE][:15]
            print(f"✅ Analisando {len(lista_final)} jogos selecionados...")

            for j in lista_final:
                f_id = j['fixture']['id']
                nome_jogo = f"{j['teams']['home']['name']} x {j['teams']['away']['name']}"
                
                try:
                    # Busca predições detalhadas para alimentar o Poisson
                    p_url = f"https://v3.football.api-sports.io/predictions?fixture={f_id}"
                    pred_res = requests.get(p_url, headers=headers).json()
                    
                    if not pred_res.get('response'): continue
                    
                    data = pred_res['response'][0]
                    comparison = data.get('comparison', {}) # Uso do .get() para blindagem

                    # --- ⚽ CÁLCULO DE GOLS (OVER 2.5) ---
                    h_avg = float(data['teams']['home']['last_5']['goals']['for']['average'] or 1.2)
                    a_avg = float(data['teams']['away']['last_5']['goals']['for']['average'] or 1.0)
                    lambda_gols = h_avg + a_avg
                    prob_gols = round(probabilidade_over_n(lambda_gols, 2), 2)

                    # --- 🚩 CÁLCULO DE ESCANTEIOS (OVER 9.5) ---
                    # Blindagem contra erro 'corners'
                    corners_info = comparison.get('corners', {})
                    perc_home = corners_info.get('home', '50%') if corners_info else '50%'
                    if perc_home is None: perc_home = '50%'
                    
                    # Converte força ofensiva em média esperada (Lambda)
                    lambda_cantos = (float(perc_home.replace('%','')) / 10) * 2
                    prob_cantos = round(probabilidade_over_n(lambda_cantos, 9), 2)

                    # --- OUTROS MERCADOS (SIMULAÇÃO BASEADA EM IA) ---
                    prob_chutes = round(float(comparison.get('attacking', {}).get('home', '50%').replace('%','')), 2)
                    prob_cartoes = round(float(comparison.get('total', {}).get('home', '45%').replace('%','')) / 2, 2)

                    # Média de Valor (EV) para o Velocímetro
                    ev_total = round((prob_gols + prob_cantos) / 2, 2)

                    # Salva ou atualiza no banco de dados
                    cur.execute("""
                        INSERT INTO analysis_logs (
                            fixture_id, fixture_name, valor_ev, match_date, 
                            gols_ev, cantos_ev, chutes_ev, cartoes_ev, stats_resumo
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (fixture_id) DO UPDATE SET
                            valor_ev = EXCLUDED.valor_ev,
                            gols_ev = EXCLUDED.gols_ev,
                            cantos_ev = EXCLUDED.cantos_ev,
                            match_date = EXCLUDED.match_date;
                    """, (f_id, nome_jogo, ev_total, j['fixture']['date'], 
                          prob_gols, prob_cantos, prob_chutes, prob_cartoes, 
                          f"Matemática de Poisson: Gols {prob_gols}% | Cantos {prob_cantos}%"))
                    
                    conn.commit()
                    total_processado += 1

                    # ALERTA TELEGRAM (Apenas se o valor for alto)
                    if ev_total > 15:
                        msg = criar_mensagem_vip(nome_jogo, j['league']['name'], ev_total, prob_gols, "Over 2.5 / Cantos")
                        enviar_alerta(msg)

                except Exception as e_jogo:
                    print(f"⚠️ Pulando {nome_jogo} (Dados insuficientes): {e_jogo}")
                    continue

        conn.close()
        print(f"🏆 FIM! {total_processado} oportunidades analisadas com Poisson.")

    except Exception as e:
        print(f"❌ ERRO CRÍTICO NO MINERADOR: {e}")

if __name__ == "__main__":
    minerar_futuro()