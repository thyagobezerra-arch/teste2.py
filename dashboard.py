import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os
import uuid
from datetime import timedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Edge Pro Analytics", page_icon="🦁", layout="wide")

# 2. FUNÇÃO DE CONEXÃO
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
        cur.execute("SELECT id FROM users WHERE username = %s AND password = %s", (user, pwd))
        auth = cur.fetchone()
        conn.close()
        return auth is not None
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return False

# Inicializa o estado de login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- TELA DE LOGIN ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>🦁 Edge Pro Analytics</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Acessar Sistema", use_container_width=True):
            if autenticar(u, p):
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# --- DASHBOARD LOGADO ---

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = init_connection()
        # CORREÇÃO AQUI: A query agora está devidamente indentada dentro do try
        query = """
            SELECT * FROM analysis_logs 
            WHERE match_date >= NOW() - INTERVAL '3 hours' 
            ORDER BY match_date ASC 
            LIMIT 50
        """
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            df.drop_duplicates(subset=['fixture_id'], keep='first', inplace=True)
        return df
    except Exception as e:
        # Retorna DataFrame vazio se der erro na consulta
        return pd.DataFrame()

# Menu Lateral
st.sidebar.title("🦁 Painel VIP")
if st.sidebar.button("Logout"):
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
        
        # AJUSTE DE HORÁRIO: Subtrai 3h para o horário da Paraíba
        horario_br = pd.to_datetime(row['match_date']) - timedelta(hours=3)
        data_formatada = horario_br.strftime('%d/%m %H:%M')
        
        with st.expander(f"⏰ {data_formatada} | {row['fixture_name']}", expanded=True):
            
            # 1. VELOCÍMETRO GRANDE E CENTRALIZADO
            fig = go.Figure(go.Indicator(
                mode = "gauge+number", 
                value = row['valor_ev'],
                title = {'text': "VALOR ESPERADO (EV) TOTAL", 'font': {'size': 20}},
                gauge = {
                    'axis': {'range': [None, 40]}, 
                    'bar': {'color': "gold"},
                    'steps': [{'range': [0, 15], 'color': "#333"}, {'range': [15, 40], 'color': "#1a1a1a"}]
                }
            ))
            fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, margin=dict(t=50, b=20))
            st.plotly_chart(fig, use_container_width=True, key=f"g_{chave}")

            st.markdown("---")
            
            # 2. OS 4 QUADRANTES DE MERCADO
            st.markdown("### 🎯 Oportunidades por Mercado")
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.metric("⚽ Gols (Over)", f"{row.get('gols_ev', 0):.1f}%")
            with c2:
                st.metric("🚩 Escanteios", f"{row.get('cantos_ev', 0):.1f}%")
            with c3:
                st.metric("🎯 Chutes ao Gol", f"{row.get('chutes_ev', 0):.1f}%")
            with c4:
                st.metric("🟨 Cartões", f"{row.get('cartoes_ev', 0):.1f}%")
            
            st.markdown("---")
            st.info(f"💡 **Análise IA:** {row['stats_resumo']}")
            st.button("Copiar Link da Bet365", key=f"b_{chave}")
else:
    st.warning("⏳ Minerador buscando novos jogos...")