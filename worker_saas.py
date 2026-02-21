import requests
import psycopg2
import os
from datetime import datetime
import pytz

# --- MODO DE PRODUÇÃO (AUTOMÁTICO) ---
# O robô vai pegar a senha que você acabou de salvar nos Secrets
DB_URL = os.getenv("DB_URL")
API_KEY = os.getenv("API_KEY")

# Fuso Horário Paraíba
FUSO_BR = pytz.timezone('America/Sao_Paulo')

def minerar():
    data_hoje = datetime.now(FUSO_BR).strftime('%Y-%m-%d')
    print(f"🚀 Iniciando Varredura Automática: {data_hoje}")
    
    try:
        # 1. Busca na API
        url = f"https://v3.football.api-sports.io/fixtures?date={data_hoje}"
        headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        
        response = requests.get(url, headers=headers)
        jogos = response.json().get('response', [])
        
        if not jogos:
            print("⚠️ Nenhum jogo na API. (Talvez seja tarde na Europa)")
            return

        # 2. Conecta no Banco (Usando o Segredo do GitHub)
        print("🔌 Conectando ao Banco...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        cont = 0
        for jogo in jogos:
            status = jogo['fixture']['status']['short']
            if status in ['FT', 'AET', 'PEN']: continue # Pula jogos acabados

            nome = f"{jogo['teams']['home']['name']} vs {jogo['teams']['away']['name']}"
            
            # Gols
            cur.execute("""
                INSERT INTO analysis_logs (fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev, mercado_tipo, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (nome, 75.0, 1.30, 1.90, 20.0, "Gols"))
            
            cont += 1

        conn.commit()
        conn.close()
        print(f"✅ Sucesso! {cont} jogos processados.")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    minerar()