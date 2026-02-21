import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import os
import pytz 

# --- CONFIGURAÇÃO DE SEGURANÇA ---
try:
    # Tenta pegar das Secrets do Streamlit Cloud
    DB_URL = st.secrets["DB_URL"]
except:
    # Backup (caso precise rodar local) - Mas o foco agora é a nuvem
    DB_URL = os.getenv("DB_URL")

# Configuração da Página
st.set_page_config(page_title="Edge Analytics Pro", page_icon="⚽", layout="wide")

# Estilização
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ff00; }
    .stDataFrame { border: 1px solid #31333f; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def carregar_dados(tipo):
    try:
        conn = psycopg2.connect(DB_URL)
        
        # --- A MUDANÇA ESTÁ AQUI ---
        # Removi o filtro de DATA. Agora ele pega os últimos 50 jogos, não importa quando foram criados.
        query = f"""
            SELECT fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev, created_at 
            FROM analysis_logs 
            WHERE mercado_tipo LIKE '%{tipo}%' 
            ORDER BY created_at DESC 
            LIMIT 50
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Ainda não há dados ou houve erro: {e}")
        return pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.title("Edge Analytics")
mercado_selecionado = st.sidebar.selectbox("Filtro de Mercado", ["Escanteios", "Gols"])

# --- CORPO PRINCIPAL ---
st.title(f"💎 Ranking: {mercado_selecionado}")

# Busca os dados
df = carregar_dados(mercado_selecionado)

if not df.empty:
    # Mostra os dados sem frescura
    st.success(f"Encontramos {len(df)} jogos no banco de dados!")
    
    # Formata para ficar bonito
    df_visual = df.rename(columns={
        'fixture_name': 'Jogo',
        'valor_ev': 'Valor EV',
        'odd_mercado': 'Odd Bet365',
        'created_at': 'Horário da Análise'
    })
    
    st.dataframe(df_visual, use_container_width=True, hide_index=True)
else:
    st.warning("O banco de dados conectou, mas a tabela está vazia.")
    st.info("Dica: Rode o arquivo 'worker_saas.py' no seu computador mais uma vez para enviar dados novos.")

# Rodapé com hora certa
fuso_br = pytz.timezone('America/Sao_Paulo')
st.caption(f"Atualizado em: {datetime.now(fuso_br).strftime('%H:%M:%S')}")