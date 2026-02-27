import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os
import uuid
from datetime import timedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Edge Pro Analytics", page_icon="🦁", layout="wide")

# 2. FUNÇÃO DE CONEXÃO (Deve vir primeiro para evitar NameError)
def init_connection():
    db_url = os.getenv("DB_URL") or st.secrets.get("DB_URL")
    if not db_url:
        # Fallback manual se os secrets falharem
        db_url = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
    return psycopg2.connect(db_url)

# 3. SISTEMA DE AUTENTICAÇÃO
def autenticar(user, pwd):
    try:
        conn = init_connection()
        cur = conn.cursor()
        # Verifica na tabela 'users' que criamos no Supabase
        cur.execute("SELECT id FROM users WHERE username = %s AND password = %s", (user, pwd))
        auth = cur.fetchone()
        conn.close()
        return auth is not None
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
        return False

# Inicializa o estado de login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- TELA DE LOGIN ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>🦁 Edge Pro Analytics</h1>", unsafe_allow_html=True)
    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("login_form"):
                u = st.text_input("Usuário")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if autenticar(u, p):
                        st.session_state['logged_in'] = True
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
    st.stop() # Bloqueia o resto do app até logar

# --- SE CHEGOU AQUI, ESTÁ LOGADO! EXIBIR DASHBOARD ---

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

# Layout do Painel
st.sidebar.title("🦁 Filtros Edge Pro")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

df = load_data()

st.markdown("# 🦁 Painel de Inteligência Esportiva")
st.markdown("---")

if not df.empty:
    ev_minimo = st.sidebar.slider("EV Mínimo %", 0, 50, 10)
    df_filtrado = df[df['valor_ev'] >= ev_minimo]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Jogos Analisados", len(df_filtrado))
    c2.metric("EV Médio", f"{df_filtrado['valor_ev'].mean():.1f}%")
    c3.metric("Oportunidades", len(df_filtrado[df_filtrado['valor_ev'] > 15]))

    st.markdown("### 🎯 Próximos Jogos com Valor")

    for i, row in df_filtrado.iterrows():
        chave_unica = str(uuid.uuid4())
        
        # --- AJUSTE DE HORÁRIO PARA BRASÍLIA (UTC-3) ---
        # Subtrai 3 horas do horário UTC da API
        horario_br = pd.to_datetime(row['match_date']) - timedelta(hours=3)
        data_jogo = horario_br.strftime('%d/%m %H:%M')
        
        with st.expander(f"⏰ {data_jogo} | {row['fixture_name']} | EV: {row['valor_ev']:.2f}%", expanded=True):
            col_graf, col_info, col_btn = st.columns([1, 2, 1])
            
            with col_graf:
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number", value = row['valor_ev'],
                    gauge = {'axis': {'range': [None, 40]}, 'bar': {'color': "green"}}
                ))
                fig.update_layout(height=200, paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
                st.plotly_chart(fig, use_container_width=True, key=f"g_{chave_unica}")
            
            with col_info:
                st.markdown(f"**Probabilidade:** `{row['probabilidade']}%` | **Odd:** `{row['odd_mercado']}`")
                st.info(f"💡 {row['stats_resumo']}")
            
            with col_btn:
                st.button("Ver Odds", key=f"b_{chave_unica}")
else:
    st.warning("⏳ Aguardando novos jogos...")