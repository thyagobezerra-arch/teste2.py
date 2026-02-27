import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os
import uuid
from datetime import timedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Edge Pro Analytics", page_icon="🦁", layout="wide")

# 2. FUNÇÃO DE CONEXÃO (Definida no topo para evitar NameError)
def init_connection():
    db_url = os.getenv("DB_URL") or st.secrets.get("DB_URL")
    if not db_url:
        db_url = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
    return psycopg2.connect(db_url)

# 3. SISTEMA DE LOGIN
def autenticar(user, pwd):
    try:
        conn = init_connection()
        cur = conn.cursor()
        # Busca o usuário e senha exatos
        cur.execute("SELECT id FROM users WHERE username = %s AND password = %s", (user, pwd))
        auth = cur.fetchone()
        conn.close()
        return auth is not None
    except Exception as e:
        st.error(f"Erro técnico no login: {e}")
        return False

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- TELA DE ACESSO ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>🦁 Edge Pro Analytics</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Sistema"):
                if autenticar(u, p):
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
    st.stop()

# --- DASHBOARD (SÓ CARREGA SE LOGADO) ---

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = init_connection()
        query = "SELECT * FROM analysis_logs ORDER BY match_date ASC LIMIT 100"
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            df.drop_duplicates(subset=['fixture_id'], keep='first', inplace=True)
        return df
    except:
        return pd.DataFrame()

st.sidebar.title("🦁 Painel VIP")
if st.sidebar.button("Sair"):
    st.session_state['logged_in'] = False
    st.rerun()

df = load_data()

st.markdown("# 🦁 Inteligência Esportiva")
st.markdown("---")

if not df.empty:
    ev_minimo = st.sidebar.slider("Filtrar EV % Mínimo", 0, 50, 10)
    df_filtrado = df[df['valor_ev'] >= ev_minimo]

    for i, row in df_filtrado.iterrows():
        chave = str(uuid.uuid4())
        
        # AJUSTE DE HORÁRIO: Subtrai 3h do UTC para chegar ao horário da Paraíba
        horario_br = pd.to_datetime(row['match_date']) - timedelta(hours=3)
        data_formatada = horario_br.strftime('%d/%m %H:%M')
        
        with st.expander(f"⏰ {data_formatada} | {row['fixture_name']} | EV: {row['valor_ev']:.2f}%", expanded=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                fig = go.Figure(go.Indicator(mode="gauge+number", value=row['valor_ev'], gauge={'axis': {'range': [None, 40]}, 'bar': {'color': "green"}}))
                fig.update_layout(height=180, paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
                st.plotly_chart(fig, use_container_width=True, key=f"g_{chave}")
            with c2:
                st.write(f"**Odd Mercado:** `{row['odd_mercado']}` | **Probabilidade:** `{row['probabilidade']}%`")
                st.info(f"💡 {row['stats_resumo']}")
            with c3:
                st.button("Análise Detalhada", key=f"b_{chave}")
else:
    st.warning("⏳ Minerador buscando novos jogos...")