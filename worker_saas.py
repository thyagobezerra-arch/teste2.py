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

def poisson_cumulative(lambda_val, k):
    """Calcula a probabilidade acumulada de acontecer ATÉ k eventos."""
    soma = 0
    for i in range(k + 1):
        soma += (math.exp(-lambda_val) * (lambda_val**i)) / math.factorial(i)
    return soma

def minerar_dados_reais():
    print("🦁 MINERADOR PRO: EXTRAINDO ESTATÍSTICAS REAIS POR TIME")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        # Foco no Sábado (Dia 28)
        data_alvo = "2026-02-28"
        print(f"📅 Analisando grade de: {data_alvo}")
        
        res = requests.get(f"https://v3.football.api-sports.io/fixtures?date={data_alvo}", headers=headers).json()
        jogos = res.get('response', [])
        
        # Vamos pegar 20 jogos variados para garantir qualidade sem estourar a cota
        # (Se tiver cota sobrando, aumente o slice [:20])
        total_processado = 0
        
        for j in jogos[:25]:
            f_id = j['fixture']['id']
            nome_jogo = f"{j['teams']['home']['name']} x {j['teams']['away']['name']}"
            
            try:
                # 1. BUSCA DADOS PROFUNDOS (PREDICTIONS)
                pred_url = f"https://v3.football.api-sports.io/predictions?fixture={f_id}"
                p_res = requests.get(pred_url, headers=headers).json()
                
                if not p_res.get('response'): continue
                dados = p_res['response'][0]

                # 2. EXTRAÇÃO DE MÉDIAS REAIS (GOLS)
                # Pega a média de gols marcados nos últimos 5 jogos
                try:
                    media_home = float(dados['teams']['home']['last_5']['goals']['for']['average'])
                    media_away = float(dados['teams']['away']['last_5']['goals']['for']['average'])
                except:
                    media_home, media_away = 1.2, 1.0 # Fallback se for time muito pequeno

                # Lambda Esperado = (Média Casa + Média Fora)
                lambda_gols = media_home + media_away
                
                # 3. CÁLCULO DE PROBABILIDADES ESPECÍFICAS
                prob_over_15 = (1 - poisson_cumulative(lambda_gols, 1)) * 100
                prob_over_25 = (1 - poisson_cumulative(lambda_gols, 2)) * 100
                
                # 4. CÁLCULO DE ESCANTEIOS (PROJEÇÃO)
                # A API Free dá a % de comparação. Usamos isso para projetar a média.
                # Média base de uma liga é ~9.5. Ajustamos pela força dos times.
                comp_cantos = dados.get('comparison', {}).get('corners', {})
                forca_home = float(comp_cantos.get('home', '50%').replace('%','')) if comp_cantos else 50
                
                # Se o time da casa tem 60% de força em cantos, a média do jogo tende a subir
                media_estimada_cantos = 9.0 * (1 + ((forca_home - 50)/100))
                prob_cantos_over_95 = (1 - poisson_cumulative(media_estimada_cantos, 9)) * 100

                # 5. FORMATAÇÃO DO TEXTO PROFISSIONAL
                # Criamos um resumo técnico para aparecer no dashboard
                resumo_tecnico = (
                    f"Média Gols: {lambda_gols:.2f} | "
                    f"Over 1.5: {prob_over_15:.0f}% | "
                    f"Over 2.5: {prob_over_25:.0f}% | "
                    f"Exp. Cantos: ~{media_estimada_cantos:.1f}"
                )

                # 6. SALVA NO BANCO
                # Usamos gols_ev para Over 1.5 e valor_ev para uma média geral
                ev_geral = (prob_over_15 + prob_cantos_over_95) / 2
                
                cur.execute("""
                    INSERT INTO analysis_logs (fixture_id, fixture_name, valor_ev, match_date, gols_ev, cantos_ev, stats_resumo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (fixture_id) 
                    DO UPDATE SET 
                        valor_ev = EXCLUDED.valor_ev,
                        gols_ev = EXCLUDED.gols_ev,
                        cantos_ev = EXCLUDED.cantos_ev,
                        stats_resumo = EXCLUDED.stats_resumo;
                """, (f_id, nome_jogo, ev_geral, j['fixture']['date'], prob_over_25, prob_cantos_over_95, resumo_tecnico))
                
                conn.commit()
                total_processado += 1
                print(f"✅ {nome_jogo} -> Gols: {lambda_gols:.1f} | Cantos: {media_estimada_cantos:.1f}")
                
            except Exception as e:
                print(f"⚠️ Erro ao processar {nome_jogo}: {e}")
                continue

        conn.close()
        print(f"🏆 SUCESSO! {total_processado} jogos com estatísticas REAIS calculadas.")
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")

if __name__ == "__main__":
    minerar_dados_reais()