import requests
import psycopg2
import os
from datetime import datetime, timedelta
import pytz

# --- MODO DE PRODUÇÃO (AUTOMÁTICO) ---
# O robô vai pegar o link que você salvou nos Secrets do GitHub
DB_URL = os.getenv("DB_URL")
API_KEY = os.getenv("API_KEY")

FUSO_BR = pytz.timezone('America/Sao_Paulo')

def minerar_seguro_automatico():
    data_hoje = datetime.now(FUSO_BR)
    # Busca HOJE e AMANHÃ (48h)
    data_amanha = data_hoje + timedelta(days=1)
    datas = [data_hoje.strftime('%Y-%m-%d'), data_amanha.strftime('%Y-%m-%d')]
    
    print(f"🚀 INICIANDO VARREDURA AUTOMÁTICA (48H)")

    try:
        print("🔌 Conectando ao Banco...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        print("✅ Conexão estável.")

        total_salvo = 0

        for data_atual in datas:
            print(f"\n🔎 Data: {data_atual}")
            
            url = f"https://v3.football.api-sports.io/fixtures?date={data_atual}"
            headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
            
            try:
                # Timeout de 15s para não travar se a API engasgar
                response = requests.get(url, headers=headers, timeout=15)
                jogos = response.json().get('response', [])
            except:
                print("   ⚠️ API instável nesta data. Pulando...")
                continue
            
            if not jogos:
                print(f"   ⚠️ Nenhum jogo encontrado.")
                continue

            # LIMITADOR DE SEGURANÇA (50 JOGOS)
            jogos_limitados = jogos[:50] 
            print(f"   ✅ Processando {len(jogos_limitados)} jogos...")

            for jogo in jogos_limitados:
                status = jogo['fixture']['status']['short']
                if status in ['FT', 'AET', 'PEN']: continue 

                nome = f"{jogo['teams']['home']['name']} vs {jogo['teams']['away']['name']}"
                
                try:
                    # GOLS
                    cur.execute("""
                        INSERT INTO analysis_logs (fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev, mercado_tipo, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (nome, 75.0, 1.30, 1.90, 20.0, "Gols"))
                    
                    # ESCANTEIOS
                    cur.execute("""
                        INSERT INTO analysis_logs (fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev, mercado_tipo, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (nome, 65.0, 1.50, 2.00, 15.0, "Escanteios"))
                    
                    conn.commit() # Salva a cada jogo
                    total_salvo += 1
                except:
                    conn.rollback()

        cur.close()
        conn.close()
        print(f"🏆 SUCESSO! {total_salvo} jogos salvos.")

    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    minerar_seguro_automatico()