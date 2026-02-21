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
    # Backup para rodar localmente no VS Code
    DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:0LMMYBrja3phgofg@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

# Configuração da Página
st.set_page_config(page_title="Edge Analytics Pro", page_icon="⚽", layout="wide")

# Estilização CSS para o Modo Dark
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
        # Filtro de data ajustado para evitar erros de fuso horário
        query = f"""SELECT fixture_name, probabilidade, odd_justa, odd_mercado, valor_ev 
                   FROM analysis_logs 
                   WHERE mercado_tipo LIKE '%{tipo}%' 
                   AND created_at >= (CURRENT_DATE - INTERVAL '1 day')
                   ORDER BY created_at DESC, valor_ev DESC LIMIT 50"""
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro de conexão com o banco: {e}")
        return pd.DataFrame()

# --- SIDEBAR (BARRA LATERAL) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/53/53244.png", width=80)
st.sidebar.title("Edge Analytics")
st.sidebar.markdown("---")

mercado_selecionado = st.sidebar.selectbox(
    "Filtro de Mercado", 
    ["Escanteios", "Gols"]
)

# --- CORPO PRINCIPAL ---
st.title(f"💎 Ranking de Valor: {mercado_selecionado}")

df = carregar_dados(mercado_selecionado)

if not df.empty:
    df['ROI %'] = (df['valor_ev'] / df['odd_justa']) * 100
    m1, m2, m3 = st.columns(3)
    m1.metric("Oportunidades", len(df[df['valor_ev'] > 0]))
    m2.metric("ROI Máximo", f"{df['ROI %'].max():.1f}%")
    m3.metric("Maior Odd", f"{df['odd_mercado'].max():.2f}")

    st.markdown("---")
    
    df_final = df.rename(columns={
        'fixture_name': 'Confronto',
        'probabilidade': 'Prob. (%)',
        'odd_justa': 'Odd Justa',
        'odd_mercado': 'Odd Bet365',
        'valor_ev': 'Vantagem (Pts)'
    })

    st.dataframe(df_final, use_container_width=True, hide_index=True)

else:
    st.warning(f"Nenhum jogo de {mercado_selecionado} encontrado.")
    st.info("Execute o minerador na aba 'Actions' do GitHub.")

# --- AJUSTE DE HORÁRIO PARA JOÃO PESSOA ---
fuso_br = pytz.timezone('America/Sao_Paulo')
horario_br = datetime.now(fuso_br).strftime('%H:%M:%S')

st.caption(f"Sistema Edge Analytics | João Pessoa-PB | Atualizado em: {horario_br}")