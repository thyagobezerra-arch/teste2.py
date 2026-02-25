import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz
import math

# ==============================================================================
# COLE SEU LINK DO SUPABASE AQUI
DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

# API Key
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
# ==============================================================================

FUSO_BR = pytz.timezone('America/Sao_Paulo')

# LISTA VIP (As ligas que aparecem no topo)
LIGAS_ELITE = [39, 140, 78, 135, 61, 71, 2, 13, 11, 4, 9, 3] # PL, LaLiga, SerieA, BR, Champions, Liberta...

def calcular_poisson(media_casa, media_fora):
    """Calcula probabilidade de Over 1.5 e 2.5"""
    try:
        lamb = (float(media_casa) + float(media_fora))
        prob_0 = math.exp(-lamb) * (lamb**0) / 1
        prob_1 = math.exp(-lamb) * (lamb**1) / 1
        prob_2 = math.exp(-lamb) * (lamb**2) / 2
        
        prob_over_15 = (1 - (prob_0 + prob_1)) * 100
        prob_over_25 = (1 - (prob_0 + prob_1 + prob_2)) * 100
        
        return min(round(prob_over_15, 1), 99.0), min(round(prob_over_25, 1), 99.0)
    except:
        return 0.0, 0.0

def minerar_hibrido_pro():
    print("🚀 INICIANDO MINERADOR HÍBRIDO (ELITE FIRST)")
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Garante tabela
        cur.execute("CREATE TABLE IF NOT EXISTS analysis_logs (id SERIAL PRIMARY KEY, fixture_name TEXT, probabilidade FLOAT, odd_justa FLOAT, odd_mercado FLOAT, valor_ev FLOAT, mercado_tipo TEXT, fixture_id INTEGER, stats_resumo TEXT, created_at TIMESTAMP DEFAULT NOW());")
        
        # Busca Hoje e Amanhã
        data_hoje = datetime.now(FUSO_BR)
        datas = [data_hoje.strftime('%Y-%m-%d'), (data_hoje + timedelta(days=1)).strftime('%Y-%m-%d')]

        total = 0

        for data_atual in datas:
            print(f"\n🔎 Data: {data_atual}")
            url = f"https://v3.football.api-sports.io/fixtures?date={data_atual}"
            headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
            
            try:
                jogos = requests.get(url, headers=headers, timeout=20).json().get('response', [])
            except:
                continue

            if not jogos: continue

            # --- FILTRO INTELIGENTE ---
            # 1. Tenta pegar jogos de Elite
            jogos_para_processar = [j for j in jogos if j['league']['id'] in LIGAS_ELITE and j['fixture']['status']['short'] == 'NS']
            
            # 2. Se tiver poucos jogos de Elite (< 5), completa com jogos "Mundiais"
            if len(jogos_para_processar) < 5:
                print("   ⚠️ Pouca Elite hoje. Completando com jogos mundiais...")
                resto_mundo = [j for j in jogos if j['league']['id'] not in LIGAS_ELITE and j['fixture']['status']['short'] == 'NS'][:10]
                jogos_para_processar.extend(resto_mundo)
            
            print(f"   ✅ Processando {len(jogos_para_processar)} jogos selecionados...")

            for j in jogos_para_processar:
                f_id = j['fixture']['id']
                time_casa = j['teams']['home']['name']
                time_fora = j['teams']['away']['name']
                liga = j['league']['name']
                
                # Cache
                cur.execute("SELECT id FROM analysis_logs WHERE fixture_id = %s", (f_id,))
                if cur.fetchone(): continue

                print(f"      🧮 Analisando: {time_casa} vs {time_fora}...")
                
                try:
                    res = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers).json()
                    if not res['response']: continue
                    p = res['response'][0]
                    
                    # Médias
                    mc = float(p['teams']['home']['last_5']['goals']['for']['average'] or 0.8)
                    mf = float(p['teams']['away']['last_5']['goals']['for']['average'] or 0.8)
                    
                    # Matemática
                    ov15, ov25 = calcular_poisson(mc, mf)
                    favorito = time_casa if mc > mf else time_fora
                    
                    # Texto Profissional
                    stats_texto = (
                        f"Favorito: **{favorito}** | "
                        f"[OV15]{ov15}[/OV15] "
                        f"[OV25]{ov25}[/OV25] "
                        f"IA: {p['predictions']['advice']}"
                    )
                    
                    # Nome com ícone de Elite se for o caso
                    icone = "⭐" if j['league']['id'] in LIGAS_ELITE else "⚽"
                    nome_display = f"{icone} {liga} | {time_casa} vs {time_fora}"
                    
                    # Salva
                    cur.execute("""
                        INSERT INTO analysis_logs (fixture_id, fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev, mercado_tipo, stats_resumo, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (f_id, nome_display, ov25, 1.50, 1.90, 15.0, "Gols", stats_texto))
                    
                    conn.commit()
                    total += 1
                except:
                    pass

        conn.close()
        print(f"\n🏆 SUCESSO! {total} jogos processados.")

    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    minerar_hibrido_pro()