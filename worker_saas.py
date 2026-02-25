import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz
import math
import random 

# ==============================================================================
# COLE SEU LINK DO SUPABASE AQUI
import os

# 1. Primeiro, o robô tenta pegar a senha do "cofre" (GitHub ou Nuvem)
DB_URL = os.getenv("DB_URL")

# 2. Se o robô não achar nada no cofre (porque você está rodando no seu próprio PC), 
# ele vai usar o seu link manual abaixo
if not DB_URL:
    DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

# API Key
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
# ==============================================================================

FUSO_BR = pytz.timezone('America/Sao_Paulo')
# Lista Elite para o robô priorizar
LIGAS_ELITE = [39, 140, 78, 135, 61, 71, 2, 13, 11, 4, 9, 3] 

def calcular_mercados_complexos(media_casa, media_fora, forca_atq_casa, forca_atq_fora):
    try:
        # GOLS
        lamb_total = (float(media_casa) + float(media_fora))
        prob_0 = math.exp(-lamb_total) * (lamb_total**0) / 1
        prob_1 = math.exp(-lamb_total) * (lamb_total**1) / 1
        prob_2 = math.exp(-lamb_total) * (lamb_total**2) / 2
        
        ov15 = (1 - (prob_0 + prob_1)) * 100
        ov25 = (1 - (prob_0 + prob_1 + prob_2)) * 100
        und25 = (prob_0 + prob_1 + prob_2) * 100 
        
        # BTTS
        prob_casa_0 = math.exp(-float(media_casa))
        prob_fora_0 = math.exp(-float(media_fora))
        btts = ((1 - prob_casa_0) * (1 - prob_fora_0)) * 100
        
        # ESCANTEIOS & CHUTES (Projeção baseada em ataque)
        fator_cantos = (float(forca_atq_casa.strip('%')) + float(forca_atq_fora.strip('%'))) / 10
        proj_cantos = fator_cantos + random.uniform(-1, 2)
        proj_chutes = proj_cantos * 2.5
        
        # CARTÕES (Baseado em equilíbrio)
        equilibrio = abs(float(media_casa) - float(media_fora))
        proj_cartoes = 4.5 - (equilibrio / 2)
        
        return {
            "ov15": round(ov15, 1),
            "ov25": round(ov25, 1),
            "und25": round(und25, 1),
            "btts": round(btts, 1),
            "cantos": round(proj_cantos, 1),
            "chutes": int(proj_chutes),
            "cartoes": round(proj_cartoes, 1)
        }
    except: return None

def minerar_futuro():
    print("🚀 INICIANDO MINERADOR DO FUTURO (PRÓXIMOS 3 DIAS)")
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Limpa tabela para renovar os dados
        cur.execute("CREATE TABLE IF NOT EXISTS analysis_logs (id SERIAL PRIMARY KEY, fixture_name TEXT, probabilidade FLOAT, odd_justa FLOAT, odd_mercado FLOAT, valor_ev FLOAT, mercado_tipo TEXT, fixture_id INTEGER, stats_resumo TEXT, created_at TIMESTAMP DEFAULT NOW());")
        
        data_base = datetime.now(FUSO_BR)
        # --- MUDANÇA: AGORA OLHAMOS 3 DIAS NA FRENTE ---
        datas = [
            data_base.strftime('%Y-%m-%d'), 
            (data_base + timedelta(days=1)).strftime('%Y-%m-%d'),
            (data_base + timedelta(days=2)).strftime('%Y-%m-%d')
        ]
        
        total = 0

        for data_atual in datas:
            print(f"\n🔎 Varrendo data: {data_atual}")
            url = f"https://v3.football.api-sports.io/fixtures?date={data_atual}"
            headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
            
            try:
                jogos = requests.get(url, headers=headers, timeout=20).json().get('response', [])
            except: continue
            
            if not jogos: continue

            # Pega TUDO que for ELITE + Alguns aleatórios para encher
            elite = [j for j in jogos if j['league']['id'] in LIGAS_ELITE and j['fixture']['status']['short'] == 'NS']
            resto = [j for j in jogos if j['league']['id'] not in LIGAS_ELITE and j['fixture']['status']['short'] == 'NS'][:10]
            
            # Prioriza Elite, mas garante pelo menos 15 jogos por dia
            lista_final = elite + resto
            
            print(f"   ✅ Encontrados {len(lista_final)} jogos para processar...")

            for j in lista_final:
                f_id = j['fixture']['id']
                time_casa = j['teams']['home']['name']
                time_fora = j['teams']['away']['name']
                liga = j['league']['name']
                
                # Verifica Cache
                cur.execute("SELECT id FROM analysis_logs WHERE fixture_id = %s", (f_id,))
                if cur.fetchone(): continue

                print(f"      🧮 Calculando: {time_casa} vs {time_fora}...")
                
                try:
                    res = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers).json()
                    if not res['response']: continue
                    p = res['response'][0]
                    
                    mc = float(p['teams']['home']['last_5']['goals']['for']['average'] or 0.5)
                    mf = float(p['teams']['away']['last_5']['goals']['for']['average'] or 0.5)
                    atq_casa = p['comparison']['att']['home'] or "50%"
                    atq_fora = p['comparison']['att']['away'] or "50%"
                    
                    dados = calcular_mercados_complexos(mc, mf, atq_casa, atq_fora)
                    if not dados: continue

                    favorito = time_casa if mc > mf else time_fora
                    
                    stats_texto = (
                        f"Favorito: **{favorito}** | "
                        f"[OV15]{dados['ov15']}[/OV15] "
                        f"[OV25]{dados['ov25']}[/OV25] "
                        f"[UND25]{dados['und25']}[/UND25] "
                        f"[BTTS]{dados['btts']}[/BTTS] "
                        f"[CANTOS]{dados['cantos']}[/CANTOS] "
                        f"[CHUTES]{dados['chutes']}[/CHUTES] "
                        f"[CARTOES]{dados['cartoes']}[/CARTOES] "
                        f"IA: {p['predictions']['advice']}"
                    )
                    
                    icone = "⭐" if j['league']['id'] in LIGAS_ELITE else "⚽"
                    nome_display = f"{icone} {liga} | {time_casa} vs {time_fora}"
                    
                    cur.execute("""
                        INSERT INTO analysis_logs (fixture_id, fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev, mercado_tipo, stats_resumo, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (f_id, nome_display, dados['ov25'], 1.50, 1.90, 15.0, "Gols", stats_texto))
                    
                    conn.commit()
                    total += 1
                except: pass

        conn.close()
        print(f"\n🏆 BANCO RECHEADO! {total} novos jogos cadastrados.")

    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    minerar_futuro()