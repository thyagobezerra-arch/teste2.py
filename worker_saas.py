import math
import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
FUSO_BR = pytz.timezone('America/Sao_Paulo')

def minerar_futuro():
    print("🦁 MODO DIAGNÓSTICO ATIVADO")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        # ESTRATÉGIA DE EMERGÊNCIA: Busca os PRÓXIMOS 50 JOGOS de qualquer liga
        # O endpoint 'next' é mais estável que o de 'date' quando a cota está baixa
        print("📡 Consultando API (Endpoint: Next 50)...")
        res = requests.get("https://v3.football.api-sports.io/fixtures?next=50", headers=headers).json()
        
        # VERIFICA ERROS DE COTA (API LIMIT)
        if res.get('errors'):
            print(f"❌ ERRO DA API: {res['errors']}")
            if 'requests' in str(res['errors']):
                print("🚨 VOCÊ ATINGIU O LIMITE DE 100 CHAMADAS/DIA. O robô só voltará a funcionar após a meia-noite.")
            return

        jogos = res.get('response', [])
        print(f"📊 API retornou {len(jogos)} jogos futuros.")

        total_salvo = 0
        for j in jogos:
            f_id = j['fixture']['id']
            nome_jogo = f"{j['league']['name']} | {j['teams']['home']['name']} x {j['teams']['away']['name']}"
            
            # Cálculo de Poisson Fixo (Para não gastar chamadas extras de predição e economizar sua cota)
            prob_g = 65.0
            prob_c = 55.0

            cur.execute("""
                INSERT INTO analysis_logs (fixture_id, fixture_name, valor_ev, match_date, gols_ev, cantos_ev, stats_resumo)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (fixture_id) 
                DO UPDATE SET valor_ev = EXCLUDED.valor_ev;
            """, (f_id, nome_jogo, 12.5, j['fixture']['date'], prob_g, prob_c, "Cálculo em processamento..."))
            
            conn.commit()
            total_salvo += 1

        conn.close()
        print(f"🏆 SUCESSO! {total_salvo} jogos injetados no banco.")
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")

if __name__ == "__main__":
    minerar_futuro()