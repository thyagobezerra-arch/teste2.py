import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os
import uuid
from datetime import timedelta

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira linha)
st.set_page_config(page_title="Edge Pro Analytics", page_icon="🦁", layout="wide")

# 2. FUNÇÃO DE CONEXÃO
def init_connection():
    db_url = os.getenv("DB_URL") or st.secrets.get("DB_URL")
    if not db_url:
        db_url = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
    return psycopg2.connect(db_url)

# 3. SISTEMA DE LOGIN COM FEEDBACK
def autenticar(user, pwd):
    try:
        conn = init_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s AND password = %s", (user, pwd))
        auth = cur.fetchone()
        conn.close()
        return auth is not None
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return False

# Inicializa a sessão
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- LÓGICA DE NAVEGAÇÃO ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>🦁 Edge Pro Analytics</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Removi o 'with st.form' para o botão ser mais responsivo
        u = st.text_input("Usuário", key="user")
        p = st.text_input("Senha", type="password", key="pass")
        
        if st.button("Acessar Sistema", use_container_width=True):
            if autenticar(u, p):
                st.session_state['logged_in'] = True
                st.success("Acesso confirmado! Entrando...")
                st.rerun() # Força o site a recarregar já logado
            else:
                st.error("Usuário ou senha incorretos. Tente novamente.")
    st.stop()

# --- DAQUI PARA BAIXO: SÓ O QUE APARECE DEPOIS DO LOGIN ---

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

# Sidebar para o usuário saber que entrou
st.sidebar.success(f"🦁 Logado: {st.session_state.get('user', 'Thyago')}")
if st.sidebar.button("Sair do Sistema"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- PAINEL PRINCIPAL ---
st.markdown("# 🦁 Inteligência Esportiva")
st.markdown("---")

df = load_data()

if not df.empty:
    ev_minimo = st.sidebar.slider("Filtrar por EV %", 0, 50, 10)
    df_filtrado = df[df['valor_ev'] >= ev_minimo]

    for i, row in df_filtrado.iterrows():
        chave = str(uuid.uuid4())
        
        # HORÁRIO BRASIL (UTC-3): O jogo de 00:30 vira 21:30 do dia anterior
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
                st.button("Copiar Análise", key=f"b_{chave}")
else:
    st.warning("⏳ O minerador está buscando novas oportunidades...")