import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz
import math
import random 
from telegram_bot import enviar_alerta, criar_mensagem_vip

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================
DB_URL = os.getenv("DB_URL") or "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
FUSO_BR = pytz.timezone('America/Sao_Paulo')
LIGAS_ELITE = [39, 140, 78, 135, 61, 71, 2, 13, 11, 4, 9, 3] 

def minerar_futuro():
    print("🚀 INICIANDO MINERADOR (VERSÃO BLINDADA)")
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Garante que a tabela existe
        cur.execute("CREATE TABLE IF NOT EXISTS analysis_logs (id SERIAL PRIMARY KEY, fixture_name TEXT, probabilidade FLOAT, odd_justa FLOAT, odd_mercado FLOAT, valor_ev FLOAT, mercado_tipo TEXT, fixture_id INTEGER, stats_resumo TEXT, created_at TIMESTAMP DEFAULT NOW());")
        conn.commit()

        # --- TESTE DE FORÇA BRUTA (Para matar o "Banco Vazio") ---
        print("🧪 Inserindo jogo de teste para validar conexão...")
        cur.execute("""
            INSERT INTO analysis_logs (fixture_id, fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev, mercado_tipo, stats_resumo, created_at)
            VALUES (999, '🦁 TESTE CONEXAO | Thyago vs Robô', 75.0, 1.20, 2.00, 25.0, 'Gols', 'Se voce ver isso, a ponte entre GitHub e Supabase esta 100%!', NOW())
            ON CONFLICT DO NOTHING;
        """)
        conn.commit()

        data_atual = datetime.now(FUSO_BR).strftime('%Y-%m-%d')
        print(f"🔎 Varrendo data: {data_atual}")
        
        url = f"https://v3.football.api-sports.io/fixtures?date={data_atual}"
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        res_api = requests.get(url, headers=headers, timeout=20).json()
        jogos = res_api.get('response', [])
        
        total = 0
        if jogos:
            # Filtra apenas alguns para não estourar a API no teste
            lista_final = [j for j in jogos if j['league']['id'] in LIGAS_ELITE][:10]
            print(f"✅ Analisando {len(lista_final)} jogos de elite...")

            for j in lista_final:
                f_id = j['fixture']['id']
                time_casa = j['teams']['home']['name']
                time_fora = j['teams']['away']['name']
                liga = j['league']['name']

                # --- BUSCA DE PREDIÇÃO ---
                try:
                    p_res = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers).json()
                    if not p_res.get('response'): continue
                    
                    # Simulação de cálculo para teste rápido
                    prob_teste = 65.5
                    ev_teste = 12.5
                    
                    cur.execute("""
                        INSERT INTO analysis_logs (fixture_id, fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev, mercado_tipo, stats_resumo, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (f_id, f"⚽ {liga} | {time_casa} x {time_fora}", prob_teste, 1.45, 1.85, ev_teste, "Over 2.5", "IA: Tendência de gols"))
                    conn.commit()
                    total += 1
                    
                    # Envia Telegram se for bom
                    if ev_teste > 10:
                        msg = criar_mensagem_vip(f"{time_casa} x {time_fora}", liga, ev_teste, prob_teste, "Over 2.5")
                        enviar_alerta(msg)
                except Exception as e_inner:
                    print(f"⚠️ Erro no jogo {f_id}: {e_inner}")
                    continue

        conn.close()
        print(f"🏆 FIM! {total} jogos reais processados + 1 jogo de teste.")

    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")

if __name__ == "__main__":
    minerar_futuro()