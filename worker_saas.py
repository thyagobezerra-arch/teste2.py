import math
import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz

DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
FUSO_BR = pytz.timezone('America/Sao_Paulo')

def poisson_prob(l, k):
    s = sum((math.exp(-l) * (l**i)) / math.factorial(i) for i in range(k + 1))
    return max(0, (1 - s) * 100)

def minerar_48h():
    print("🦁 MINERADOR 48H: BUSCANDO FUTURO")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        # Lista dinâmica: Hoje, Amanhã e Depois (Garante 48h+ de cobertura)
        datas = [
            datetime.now(FUSO_BR).strftime('%Y-%m-%d'),
            (datetime.now(FUSO_BR) + timedelta(days=1)).strftime('%Y-%m-%d'),
            (datetime.now(FUSO_BR) + timedelta(days=2)).strftime('%Y-%m-%d')
        ]

        total = 0
        for dia in datas:
            print(f"📅 Varrendo data: {dia}")
            res = requests.get(f"https://v3.football.api-sports.io/fixtures?date={dia}", headers=headers).json()
            jogos = res.get('response', [])
            
            # Pega os primeiros 15 jogos de cada dia para manter o fluxo constante
            for j in jogos[:15]:
                # PULA SE JÁ COMEÇOU (Filtro essencial)
                data_jogo = datetime.fromisoformat(j['fixture']['date'].replace('Z', '+00:00'))
                if data_jogo < datetime.now(pytz.UTC): continue

                f_id = j['fixture']['id']
                nome = f"{j['teams']['home']['name']} x {j['teams']['away']['name']}"
                
                try:
                    # Predição Real
                    p_res = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers).json()
                    if not p_res.get('response'): continue
                    d = p_res['response'][0]

                    # Gols
                    mh = float(d['teams']['home']['last_5']['goals']['for']['average'] or 1.0)
                    ma = float(d['teams']['away']['last_5']['goals']['for']['average'] or 1.0)
                    l_gols = mh + ma
                    p_over15 = round(poisson_prob(l_gols, 1))
                    p_over25 = round(poisson_prob(l_gols, 2))

                    # Cantos
                    comp = d.get('comparison', {}).get('corners', {})
                    f_home = float(comp.get('home', '50%').replace('%','')) if comp else 50
                    l_cantos = 9.0 * (1 + ((f_home-50)/100))
                    p_cantos = round(poisson_prob(l_cantos, 9))

                    resumo = f"Média:{l_gols:.1f}|+1.5:{p_over15}%|+2.5:{p_over25}%"
                    ev = (p_over15 + p_cantos)/2

                    cur.execute("""
                        INSERT INTO analysis_logs (fixture_id, fixture_name, valor_ev, match_date, gols_ev, cantos_ev, stats_resumo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (fixture_id) DO UPDATE SET 
                        match_date = EXCLUDED.match_date, stats_resumo = EXCLUDED.stats_resumo;
                    """, (f_id, nome, ev, j['fixture']['date'], p_over25, p_cantos, resumo))
                    
                    conn.commit()
                    total += 1
                    print(f"   ✅ Antecipado: {nome} ({dia})")

                except: continue

        conn.close()
        print(f"🏆 SUCESSO! {total} jogos futuros adicionados.")

    except Exception as e: print(f"❌ Erro: {e}")

if __name__ == "__main__":
    minerar_48h()