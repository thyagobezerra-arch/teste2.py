import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import pytz

# --- LINK DO BANCO ---
# Tenta pegar da gaveta secreta (nuvem), se não achar, usa o link direto (local)
try:
    DB_URL = st.secrets["DB_URL"]
except:
    DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

st.set_page_config(page_title="Edge Analytics Pro", page_icon="⚽", layout="wide")

def carregar_dados(tipo):
    try:
        conn = psycopg2.connect(DB_URL)
        query = f"SELECT fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev FROM analysis_logs WHERE mercado_tipo = '{tipo}' ORDER BY created_at DESC LIMIT 20"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

st.title("⚽ Elite Football Analytics")
st.write("### Foco: Premier League, LaLiga, Bundesliga e Serie A")

# Criação das Abas
aba_gols, aba_fav = st.tabs(["🔥 Gols (Over 2.5)", "🏆 Favoritismos"])

with aba_gols:
    df_gols = carregar_dados("Gols")
    if not df_gols.empty:
        st.dataframe(df_gols, use_container_width=True, hide_index=True)
    else:
        st.info("Buscando novos jogos de Gols...")

with aba_fav:
    st.write("### ⭐ Times com maior probabilidade de vitória")
    df_fav = carregar_dados("Favoritos")
    if not df_fav.empty:
        st.dataframe(df_fav, use_container_width=True, hide_index=True)
    else:
        st.info("Aguardando análise de favoritismo...")

fuso = pytz.timezone('America/Sao_Paulo')
st.caption(f"Última atualização: {datetime.now(fuso).strftime('%d/%m %H:%M:%S')}")