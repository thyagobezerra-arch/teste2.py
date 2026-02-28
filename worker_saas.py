import math
import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz

# Configurações
DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
FUSO_BR = pytz.timezone('America/Sao_Paulo')

def poisson_prob(l, k):
    s = sum((math.exp(-l) * (l**i)) / math.factorial(i) for i in range(k + 1))
    return max(0, (1 - s) * 100)

def minerar_pro():
    print("🦁 MINERADOR PRO: LIGAS + VOLUME ALTO")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        # Datas: Hoje e Amanhã (Foco em 48h)
        datas = [
            datetime.now(FUSO_BR).strftime('%Y-%m-%d'),
            (datetime.now(FUSO_BR) + timedelta(days=1)).strftime('%Y-%m-%d')
        ]

        total_salvo = 0
        
        for dia in datas:
            print(f"📅 Varrendo data: {dia}")
            res = requests.get(f"https://v3.football.api-sports.io/fixtures?date={dia}", headers=headers).json()
            jogos = res.get('response', [])
            
            # AUMENTAMOS O LIMITADOR: De 15 para 35 jogos por dia
            # Isso garante mais volume sem estourar o limite de 100/dia da API
            for j in jogos[:35]:
                # Pula jogos que já começaram
                data_jogo = datetime.fromisoformat(j['fixture']['date'].replace('Z', '+00:00'))
                if data_jogo < datetime.now(pytz.UTC): continue

                f_id = j['fixture']['id']
                liga = j['league']['name']
                times = f"{j['teams']['home']['name']} x {j['teams']['away']['name']}"
                
                # FORMATO NOVO: "LIGA # TIMES" (Usamos # para separar fácil depois)
                nome_completo = f"{liga} #{times}"
                
                try:
                    # Chamada de Predição (Gasta 1 crédito da API)
                    p_res = requests.get(f"https://v3.football.api-sports.io/predictions?fixture={f_id}", headers=headers).json()
                    
                    # Se der erro de cota, para imediatamente para não travar a conta
                    if p_res.get('errors'): 
                        print("🚨 Limite da API atingido para hoje.")
                        break
                        
                    if not p_res.get('response'): continue
                    d = p_res['response'][0]

                    # Cálculos Poisson
                    mh = float(d['teams']['home']['last_5']['goals']['for']['average'] or 1.0)
                    ma = float(d['teams']['away']['last_5']['goals']['for']['average'] or 1.0)
                    l_gols = mh + ma
                    p_over15 = round(poisson_prob(l_gols, 1))
                    p_over25 = round(poisson_prob(l_gols, 2))

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
                        fixture_name = EXCLUDED.fixture_name,
                        match_date = EXCLUDED.match_date, 
                        stats_resumo = EXCLUDED.stats_resumo;
                    """, (f_id, nome_completo, ev, j['fixture']['date'], p_over25, p_cantos, resumo))
                    
                    conn.commit()
                    total_salvo += 1
                    print(f"   ✅ {liga}: {times}")

                except Exception as e:
                    print(f"   ⚠️ Pulei: {e}")
                    continue

        conn.close()
        print(f"🏆 SUCESSO! {total_salvo} jogos novos adicionados.")

    except Exception as e: print(f"❌ Erro Crítico: {e}")

if __name__ == "__main__":
    minerar_pro()