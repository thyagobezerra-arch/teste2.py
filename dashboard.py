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

# 3. SISTEMA DE LOGIN COM FEEDBACK VISUAL
def autenticar(user, pwd):
    try:
        conn = init_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s AND password = %s", (user, pwd))
        auth = cur.fetchone()
        conn.close()
        return auth is not None
    except Exception as e:
        st.error(f"Erro técnico de conexão: {e}")
        return False

# Inicializa a sessão
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- TELA DE ACESSO (TRAVA ATÉ LOGAR) ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>🦁 Edge Pro Analytics</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        u = st.text_input("Usuário", placeholder="Seu nome de usuário")
        p = st.text_input("Senha", type="password", placeholder="Sua senha secreta")
        
        # O botão agora é mais direto para evitar travamentos
        if st.button("🔓 Acessar Sistema", use_container_width=True):
            if autenticar(u, p):
                st.session_state['logged_in'] = True
                st.success("✅ Acesso autorizado! Abrindo painel...")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos. Verifique os dados.")
    st.stop()

# --- DAQUI PARA BAIXO: SÓ CARREGA DEPOIS DO LOGIN ---

@st.cache_data(ttl=1) # Cache de apenas 1 segundo para garantir dados novos
def load_data():
    try:
        conn = init_connection()
        # Mostramos tudo o que o minerador salvou nas últimas 24h
        query = "SELECT * FROM analysis_logs ORDER BY match_date ASC LIMIT 100"
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            df.drop_duplicates(subset=['fixture_id'], keep='first', inplace=True)
        return df
    except:
        return pd.DataFrame()

# Menu Lateral de Suporte
st.sidebar.title("🦁 Painel VIP")
if st.sidebar.button("🔄 Atualizar Grade"):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("Sair (Logout)"):
    st.session_state['logged_in'] = False
    st.rerun()

# CARREGAMENTO DOS DADOS
df = load_data()

st.markdown("# 🦁 Inteligência Esportiva")
st.markdown("---")

if not df.empty:
    ev_minimo = st.sidebar.slider("Filtro EV % Mínimo", 0, 50, 10)
    df_filtrado = df[df['valor_ev'] >= ev_minimo]
    
    st.sidebar.info(f"Monitorando {len(df_filtrado)} jogos agora.")

    for i, row in df_filtrado.iterrows():
        chave = str(uuid.uuid4())
        
        # Ajuste de Horário para João Pessoa
        horario_br = pd.to_datetime(row['match_date']) - timedelta(hours=3)
        data_formatada = horario_br.strftime('%d/%m %H:%M')
        
        with st.expander(f"⏰ {data_formatada} | {row['fixture_name']} | EV: {row['valor_ev']:.2f}%", expanded=True):
            # VELOCÍMETRO CENTRALIZADO
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
            st.markdown("### 🎯 Oportunidades por Mercado")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("⚽ Gols (Over)", f"{row.get('gols_ev', 0):.1f}%")
            with c2: st.metric("🚩 Escanteios", f"{row.get('cantos_ev', 0):.1f}%")
            with c3: st.metric("🎯 Chutes ao Gol", f"{row.get('chutes_ev', 0):.1f}%")
            with c4: st.metric("🟨 Cartões", f"{row.get('cartoes_ev', 0):.1f}%")
            
            st.info(f"💡 **Análise IA:** {row['stats_resumo']}")
else:
    st.warning("⏳ O banco de dados está sincronizando os jogos encontrados pelo minerador. Clique em 'Atualizar Grade' na lateral.")