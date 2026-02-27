import math
import requests
import psycopg2
import os
from datetime import datetime
import pytz

# Configurações (Mantenha as suas chaves)
DB_URL = os.getenv("DB_URL") or "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
API_KEY = "a38db0f256a84b4c71d294ac0e213307"

def calcular_poisson(lambda_val, x):
    """Calcula a probabilidade de ocorrer exatamente X eventos."""
    return (math.exp(-lambda_val) * (lambda_val**x)) / math.factorial(x)

def probabilidade_over_25(media_gols_partida):
    """Calcula a probabilidade de sair MAIS de 2.5 gols."""
    # P(Over 2.5) = 1 - [P(0) + P(1) + P(2)]
    p0 = calcular_poisson(media_gols_partida, 0)
    p1 = calcular_poisson(media_gols_partida, 1)
    p2 = calcular_poisson(media_gols_partida, 2)
    return (1 - (p0 + p1 + p2)) * 100

def minerar_futuro():
    print("🚀 MINERADOR COM CÁLCULO DE POISSON ATIVADO")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        data_hoje = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%Y-%m-%d')
        
        # Busca jogos de hoje
        res = requests.get(f"https://v3.football.api-sports.io/fixtures?date={data_hoje}", headers=headers).json()
        jogos = res.get('response', [])[:5] # Analisando os 5 primeiros para teste

        for j in jogos:
            f_id = j['fixture']['id']
            nome_jogo = f"{j['teams']['home']['name']} x {j['teams']['away']['name']}"
            
            # BUSCANDO ESTATÍSTICAS PARA POISSON
            # Pegamos a média de gols dos últimos jogos dos times
            pred_res = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers).json()
            
            if pred_res.get('response'):
                data = pred_res['response'][0]
                # Média de gols esperada (lambda) baseada na força de ataque/defesa
                lambda_gols = (data['teams']['home']['last_5']['goals']['for']['average'] + 
                               data['teams']['away']['last_5']['goals']['for']['average'])
                
                prob_gols = round(probabilidade_over_25(float(lambda_gols)), 2)
                
                # Para escanteios e outros, usamos as porcentagens da própria API para simplificar
                prob_cantos = float(data['comparison']['corners']['home'].replace('%','')) if data['comparison']['corners']['home'] else 0
                prob_chutes = float(data['comparison']['attacking']['home'].replace('%','')) if data['comparison']['attacking']['home'] else 0
                
                # Cálculo de EV (Exemplo: Odd de 2.00 na Bet365)
                odd_mercado = 2.00 
                ev_gols = round((prob_gols * odd_mercado) - 100, 2)

                cur.execute("""
                    INSERT INTO analysis_logs (
                        fixture_id, fixture_name, valor_ev, match_date, 
                        gols_ev, cantos_ev, chutes_ev, cartoes_ev, stats_resumo
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (fixture_id) DO NOTHING
                """, (f_id, nome_jogo, ev_gols, j['fixture']['date'], 
                      prob_gols, prob_cantos, prob_chutes, 5.0, "Poisson: Alta probabilidade baseada em médias históricas."))
                conn.commit()
                print(f"✅ Analisado: {nome_jogo} | Poisson Gols: {prob_gols}%")

        conn.close()
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    minerar_futuro()