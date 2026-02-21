import requests
import psycopg2
import os
from datetime import datetime
import pytz # Importante para corrigir o fuso horário

# Configurações
API_KEY = os.getenv("API_KEY")
DB_URL = os.getenv("DB_URL")

# Define o fuso horário do Brasil
FUSO_BR = pytz.timezone('America/Sao_Paulo')

def minerar():
    # Pega a data correta no Brasil (dia 20)
    data_hoje = datetime.now(FUSO_BR).strftime('%Y-%m-%d')
    print(f"🚀 Iniciando Varredura para a data: {data_hoje} (Horário Brasil)")
    
    url = f"https://v3.football.api-sports.io/fixtures?date={data_hoje}"
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    try:
        print(f"📡 Consultando API...")
        response = requests.get(url, headers=headers)
        
        # Verifica se a API respondeu bem
        if response.status_code != 200:
            print(f"❌ Erro na API: {response.text}")
            return

        dados = response.json()
        jogos = dados.get('response', [])
        
        if not jogos:
            print("⚠️ Nenhum jogo encontrado na API para hoje.")
            return

        print(f"🔎 Analisando {len(jogos)} jogos encontrados...")
        
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        jogos_salvos = 0
        
        for jogo in jogos:
            # Filtra apenas jogos que não começaram ou estão ao vivo (Short/Long)
            status = jogo['fixture']['status']['short']
            if status in ['FT', 'AET', 'PEN']: # Ignora jogos que já acabaram
                continue

            nome_jogo = f"{jogo['teams']['home']['name']} vs {jogo['teams']['away']['name']}"
            league_id = jogo['league']['id']
            
            # Tenta pegar as Odds (se existirem)
            # Nota: Na conta Free da API-Sports, as odds vêm em um endpoint separado, 
            # mas vamos simular a inserção para testar seu painel.
            
            # INSERÇÃO NO BANCO (GOLS)
            cur.execute("""
                INSERT INTO analysis_logs (fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev, mercado_tipo, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (nome_jogo, 75.0, 1.33, 1.80, 15.5, "Gols"))
            
            # INSERÇÃO NO BANCO (ESCANTEIOS)
            cur.execute("""
                INSERT INTO analysis_logs (fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev, mercado_tipo, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (nome_jogo, 60.0, 1.66, 2.10, 12.0, "Escanteios"))
            
            jogos_salvos += 1

        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Sucesso! {jogos_salvos} oportunidades salvas no banco de dados.")
        
    except Exception as e:
        print(f"❌ Erro Crítico: {e}")

if __name__ == "__main__":
    minerar()