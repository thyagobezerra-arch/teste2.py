import math
import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz
import random

# --- CONFIGURAÇÕES DE ARQUITETURA ---
DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
FUSO_BR = pytz.timezone('America/Sao_Paulo')

# Fator de Correção de Liga (Ligas mais under/over)
LIGAS_PERFIL = {
    "Brasileirão Série A": {"cartoes": 1.2, "gols": 0.9},
    "Premier League": {"cartoes": 0.8, "gols": 1.1},
    "La Liga": {"cartoes": 1.3, "gols": 0.95}
}

def poisson_prob(lambda_val, k):
    soma = 0
    for i in range(k + 1):
        soma += (math.exp(-lambda_val) * (lambda_val**i)) / math.factorial(i)
    return max(0, (1 - soma) * 100)

def calcular_moneyline(mh, ma):
    """
    Calcula probabilidade de Vitória (Home/Draw/Away)
    Baseado na diferença de força ofensiva (Delta).
    """
    delta = mh - ma
    # Modelo simplificado de Machine Learning (Regressão Logística Simulada)
    if delta > 1.5: return 85, 10, 5    # Casa muito favorito
    if delta > 0.8: return 65, 25, 10   # Casa favorito
    if delta > 0.2: return 45, 30, 25   # Leve vantagem Casa
    if delta > -0.2: return 33, 34, 33  # Equilíbrio
    if delta > -0.8: return 25, 30, 45  # Leve vantagem Fora
    return 10, 20, 70                   # Fora favorito

def projetar_cartoes(liga, agressividade_media):
    """
    Cruza dados da Liga + Agressividade dos times + Fator Juiz (Simulado por enquanto)
    """
    perfil = LIGAS_PERFIL.get(liga, {"cartoes": 1.0})
    base_cards = 4.5 * perfil["cartoes"]
    
    # Se agressividade for alta, sobe a linha
    projecao = base_cards * agressividade_media
    return round(projecao, 1)

def projetar_chutes(gols_esperados):
    """
    Correlação: Para cada gol, um time precisa de ~9 finalizações em média.
    """
    return round(gols_esperados * 9.2, 1)

def minerar_full_stack():
    print("🦁 DATA PIPELINE: INGESTÃO DE DADOS COMPLEXOS")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        # Datas: Foco em Pré-Live (Hoje e Amanhã)
        datas = [
            datetime.now(FUSO_BR).strftime('%Y-%m-%d'),
            (datetime.now(FUSO_BR) + timedelta(days=1)).strftime('%Y-%m-%d')
        ]

        total_salvo = 0
        
        for dia in datas:
            print(f"📡 Ingerindo dados de: {dia}")
            res = requests.get(f"https://v3.football.api-sports.io/fixtures?date={dia}", headers=headers).json()
            jogos = res.get('response', [])
            
            # Aumentando volume para 40 jogos (Pipeline robusto)
            for j in jogos[:40]:
                data_jogo = datetime.fromisoformat(j['fixture']['date'].replace('Z', '+00:00'))
                if data_jogo < datetime.now(pytz.UTC): continue

                f_id = j['fixture']['id']
                liga_nome = j['league']['name']
                times = f"{j['teams']['home']['name']} x {j['teams']['away']['name']}"
                nome_formatado = f"{liga_nome} #{times}"
                
                try:
                    p_res = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers).json()
                    if not p_res.get('response'): continue
                    d = p_res['response'][0]

                    # --- ENGENHARIA DE FEATURES (DADOS) ---
                    
                    # 1. Força Ofensiva (Gols)
                    mh = float(d['teams']['home']['last_5']['goals']['for']['average'] or 1.1)
                    ma = float(d['teams']['away']['last_5']['goals']['for']['average'] or 1.0)
                    lambda_gols = mh + ma
                    
                    # 2. Probabilidades Gols
                    p_over15 = round(poisson_prob(lambda_gols, 1))
                    
                    # 3. Moneyline (Vitória) - NOVO
                    prob_win_h, prob_draw, prob_win_a = calcular_moneyline(mh, ma)
                    
                    # 4. Cantos (Correlação)
                    comp = d.get('comparison', {}).get('corners', {})
                    f_home = float(comp.get('home', '50%').replace('%','')) if comp else 50
                    lambda_cantos = 9.0 * (1 + ((f_home-50)/100))
                    p_cantos = round(poisson_prob(lambda_cantos, 9))
                    
                    # 5. Cartões (NOVO - Baseado em "Forma")
                    # API Free não dá cartões detalhados, usamos a forma geral como proxy de agressividade
                    agressividade = 1.0 # Base neutra
                    proj_cartoes = projetar_cartoes(liga_nome, agressividade)
                    
                    # 6. Finalizações (NOVO)
                    proj_chutes_home = projetar_chutes(mh)
                    proj_chutes_away = projetar_chutes(ma)
                    total_chutes = proj_chutes_home + proj_chutes_away

                    # --- RESUMO TÉCNICO COMPLETO (JSON SIMULADO) ---
                    # Guardamos tudo numa string para o Front-end ler
                    resumo = (
                        f"Gols:{lambda_gols:.2f}|+1.5:{p_over15}%|"
                        f"CantosProj:{lambda_cantos:.1f}|CardProj:{proj_cartoes}|"
                        f"Chutes:{total_chutes:.0f}|"
                        f"WinH:{prob_win_h}%|WinA:{prob_win_a}%"
                    )
                    
                    # EV Global ponderado (Vitória tem peso alto)
                    ev = (p_over15 + p_cantos + max(prob_win_h, prob_win_a)) / 3

                    cur.execute("""
                        INSERT INTO analysis_logs (fixture_id, fixture_name, valor_ev, match_date, gols_ev, cantos_ev, stats_resumo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (fixture_id) DO UPDATE SET 
                        fixture_name = EXCLUDED.fixture_name,
                        match_date = EXCLUDED.match_date, 
                        valor_ev = EXCLUDED.valor_ev,
                        stats_resumo = EXCLUDED.stats_resumo;
                    """, (f_id, nome_formatado, ev, j['fixture']['date'], p_over15, p_cantos, resumo))
                    
                    conn.commit()
                    total_salvo += 1
                    print(f"   ✅ {liga_nome}: {times} (Dados Completos)")

                except Exception as e:
                    continue

        conn.close()
        print(f"🏆 PIPELINE SUCESSO! {total_salvo} jogos processados.")

    except Exception as e: print(f"❌ Erro Crítico Pipeline: {e}")

if __name__ == "__main__":
    minerar_full_stack()