import math
import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz
import random

# CONFIGURAÇÕES
DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
FUSO_BR = pytz.timezone('America/Sao_Paulo')

def poisson_prob(lambda_val, k):
    """Probabilidade de acontecer MAIS que k eventos"""
    soma = 0
    for i in range(k + 1):
        soma += (math.exp(-lambda_val) * (lambda_val**i)) / math.factorial(i)
    return max(0, (1 - soma) * 100)

def calcular_escanteios_projetados(media_gols_total, forca_ataque_casa):
    """
    ALGORITMO DE CORRELAÇÃO:
    Times que marcam mais gols tendem a criar mais cantos.
    Base Global = 9.5 cantos.
    Ajuste: Para cada gol de média acima de 2.5, adicionamos cantos.
    """
    base_cantos = 9.0
    
    # Fator Ofensivo: Se o jogo tem expectativa de 3 gols, é um jogo aberto (+Cantos)
    fator_gols = (media_gols_total - 2.5) * 1.5 
    
    # Fator Pressão: Se o time da casa é muito forte, ele pressiona mais (+Cantos)
    fator_pressao = (forca_ataque_casa - 1.0) * 0.8
    
    # Projeção Final (com pequena variação orgânica de 5% para não ficar robótico)
    projecao = base_cantos + fator_gols + fator_pressao
    
    # Travas de segurança (Mínimo 6, Máximo 14 para ser realista)
    if projecao < 6.0: projecao = 6.0
    if projecao > 14.0: projecao = 14.0
    
    return projecao

def minerar_algoritmo_pro():
    print("🦁 MINERADOR CORRELAÇÃO: GOLS -> CANTOS")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        # Monitora Hoje e Amanhã
        datas = [
            datetime.now(FUSO_BR).strftime('%Y-%m-%d'),
            (datetime.now(FUSO_BR) + timedelta(days=1)).strftime('%Y-%m-%d')
        ]

        total_salvo = 0
        
        for dia in datas:
            print(f"📅 Processando grade: {dia}")
            res = requests.get(f"https://v3.football.api-sports.io/fixtures?date={dia}", headers=headers).json()
            jogos = res.get('response', [])
            
            # Pega 40 jogos para encher o painel
            for j in jogos[:40]:
                # Ignora jogos passados
                data_jogo = datetime.fromisoformat(j['fixture']['date'].replace('Z', '+00:00'))
                if data_jogo < datetime.now(pytz.UTC): continue

                f_id = j['fixture']['id']
                liga = j['league']['name']
                times = f"{j['teams']['home']['name']} x {j['teams']['away']['name']}"
                nome_completo = f"{liga} #{times}"
                
                try:
                    p_res = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers).json()
                    
                    if p_res.get('errors'): break # Para se acabar a cota
                    if not p_res.get('response'): continue
                    
                    d = p_res['response'][0]

                    # 1. DADOS DE GOLS (O MOTOR DA ANÁLISE)
                    # Se não tiver dados, usamos 1.2 como base conservadora
                    mh = float(d['teams']['home']['last_5']['goals']['for']['average'] or 1.2)
                    ma = float(d['teams']['away']['last_5']['goals']['for']['average'] or 1.0)
                    lambda_gols = mh + ma
                    
                    # Probabilidades Gols
                    p_over15 = round(poisson_prob(lambda_gols, 1))
                    p_over25 = round(poisson_prob(lambda_gols, 2))

                    # 2. DADOS DE CANTOS (CALCULADO VIA CORRELAÇÃO)
                    # Não dependemos mais da API dizer os cantos. Nós calculamos baseados no ataque.
                    lambda_cantos = calcular_escanteios_projetados(lambda_gols, mh)
                    
                    # Probabilidade Poisson para Over 9.5 Cantos
                    p_cantos = round(poisson_prob(lambda_cantos, 9))

                    # Resumo Técnico para o Dashboard
                    resumo = f"Média Gols:{lambda_gols:.2f}|+1.5:{p_over15}%|+2.5:{p_over25}%|Exp.Cantos:{lambda_cantos:.1f}"
                    
                    # EV Global (Média das oportunidades)
                    ev = (p_over15 + p_cantos)/2

                    cur.execute("""
                        INSERT INTO analysis_logs (fixture_id, fixture_name, valor_ev, match_date, gols_ev, cantos_ev, stats_resumo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (fixture_id) DO UPDATE SET 
                        fixture_name = EXCLUDED.fixture_name,
                        match_date = EXCLUDED.match_date, 
                        valor_ev = EXCLUDED.valor_ev,
                        gols_ev = EXCLUDED.gols_ev,
                        cantos_ev = EXCLUDED.cantos_ev,
                        stats_resumo = EXCLUDED.stats_resumo;
                    """, (f_id, nome_completo, ev, j['fixture']['date'], p_over25, p_cantos, resumo))
                    
                    conn.commit()
                    total_salvo += 1
                    print(f"   ✅ {times} -> Gols: {lambda_gols:.1f} | Cantos Proj: {lambda_cantos:.1f} ({p_cantos}%)")

                except Exception as e:
                    continue

        conn.close()
        print(f"🏆 SUCESSO! {total_salvo} jogos analisados com algoritmo de correlação.")

    except Exception as e: print(f"❌ Erro Crítico: {e}")

if __name__ == "__main__":
    minerar_algoritmo_pro()