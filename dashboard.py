import streamlit as st
import pandas as pd
import psycopg2
import os

# --- CONEXÃO ---
try:
    DB_URL = st.secrets["DB_URL"]
except:
    DB_URL = "COLE_SEU_LINK_AQUI_PARA_TESTE_LOCAL"

st.set_page_config(page_title="Edge Analytics Elite", page_icon="🏆", layout="wide")

# CSS para melhorar o visual das tabelas
st.markdown("""
    <style>
    .stDataFrame { border: 1px solid #00ff00; border-radius: 5px; }
    h1 { color: #00ff00; }
    </style>
    """, unsafe_allow_html=True)

def buscar_dados(mercado):
    try:
        conn = psycopg2.connect(DB_URL)
        # Query que foca no nome do jogo que já contém a Liga
        query = f"""
            SELECT fixture_name as "Competição | Jogo | Data", 
                   probabilidade as "Prob. %", 
                   odd_mercado as "Odd Betano", 
                   valor_ev as "Valor EV"
            FROM analysis_logs 
            WHERE mercado_tipo = '{mercado}'
            ORDER BY created_at DESC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return pd.DataFrame()

st.title("⚽ Dashboard de Elite - Padrão Betano")

# Criando as Abas solicitadas
aba_gols, aba_fav = st.tabs(["🔥 Gols (Over 2.5)", "🏆 Favoritismos"])

with aba_gols:
    st.subheader("Oportunidades em Gols - Principais Ligas")
    dados_gols = buscar_dados("Gols")
    if not dados_gols.empty:
        st.dataframe(dados_gols, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum jogo de Elite encontrado para Gols no momento.")

with aba_fav:
    st.subheader("Análise de Favoritismo (Match Winner)")
    dados_fav = buscar_dados("Favoritos")
    if not dados_fav.empty:
        st.dataframe(dados_fav, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum jogo de Elite encontrado para Favoritos no momento.")

st.sidebar.write("### 🌍 Ligas Monitoradas:")
st.sidebar.markdown("- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League\n- 🇪🇸 La Liga\n- 🇩🇪 Bundesliga\n- 🇮🇹 Serie A\n- 🇧🇷 Brasileirão")