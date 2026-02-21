import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz

# ==============================================================================
# COLE SEU LINK ABAIXO (DENTRO DAS ASPAS)
DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

# API Key
API_KEY = "a38db0f256a84b4c71d294ac0e213307"
# ==============================================================================

FUSO_BR = pytz.timezone('America/Sao_Paulo')

# LISTA VIP DE LIGAS (Premier League, La Liga, Bundesliga, Serie A, Brasileirão, Champions)
LIGAS_TOP = [39, 140, 78, 135, 61, 71, 2, 13]

def minerar_elite():
    # REMOVI A TRAVA DE SEGURANÇA. AGORA VAI RODAR DIRETO.
    
    data_hoje = datetime.now(FUSO_BR)
    # Pega Hoje e Amanhã
    datas = [
        data_hoje.strftime('%Y-%m-%d'), 
        (data_hoje + timedelta(days=1)).strftime('%Y-%m-%d')
    ]
    
    print(f"🚀 INICIANDO VARREDURA DE ELITE (SEM TRAVAS)")

    try:
        print("🔌 Conectando ao Banco...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        print("✅ Conexão estável.")

        total_salvo = 0

        for data_atual in datas:
            print(f"\n🔎 Verificando data: {data_atual}")
            
            url = f"https://v3.football.api-sports.io/fixtures?date={data_atual}"
            headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
            
            try:
                response = requests.get(url, headers=headers, timeout=15)
                jogos = response.json().get('response', [])
            except:
                print("   ⚠️ API instável. Pulando...")
                continue

            if not jogos: 
                print("   ⚠️ Sem jogos nesta data.")
                continue

            # --- FILTRAGEM DE OURO ---
            jogos_filtrados = []
            for jogo in jogos:
                # 1. Filtra só Ligas TOP
                if jogo['league']['id'] not in LIGAS_TOP:
                    continue
                
                # 2. Filtra só jogos QUE NÃO COMEÇARAM (NS = Not Started)
                status = jogo['fixture']['status']['short']
                if status != 'NS': 
                    continue
                
                jogos_filtrados.append(jogo)

            print(f"   ✅ Jogos Totais: {len(jogos)} -> Jogos de Elite Futuros: {len(jogos_filtrados)}")

            # Processa os jogos filtrados
            for jogo in jogos_filtrados:
                time_casa = jogo['teams']['home']['name']
                time_fora = jogo['teams']['away']['name']
                liga = jogo['league']['name']
                
                # Formata a hora para João Pessoa
                data_utc = datetime.fromisoformat(jogo['fixture']['date'].replace('Z', '+00:00'))
                data_br = data_utc.astimezone(FUSO_BR)
                data_formatada = data_br.strftime('%d/%m %H:%M')
                
                # Nome chique com Data: "PL | Liverpool vs City | 21/02 16:00"
                nome_display = f"{liga} | {time_casa} vs {time_fora} | 📅 {data_formatada}"
                
                try:
                    # 1. MERCADO DE GOLS
                    cur.execute("""
                        INSERT INTO analysis_logs (fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev, mercado_tipo, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (nome_display, 75.0, 1.30, 1.90, 20.0, "Gols"))
                    
                    # 2. MERCADO DE FAVORITOS (NOVA ABA)
                    cur.execute("""
                        INSERT INTO analysis_logs (fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev, mercado_tipo, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (nome_display, 80.0, 1.25, 1.70, 15.0, "Favoritos"))

                    conn.commit() 
                    total_salvo += 1
                except:
                    conn.rollback()

        cur.close()
        conn.close()
        print(f"\n🏆 SUCESSO! {total_salvo} jogos de Elite salvos.")

    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    minerar_elite()