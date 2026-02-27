import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os
import uuid

# --- SISTEMA DE LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def autenticar(user, pwd):
    # Conecta no banco para conferir a senha
    conn = init_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s AND password = %s", (user, pwd))
    auth = cur.fetchone()
    conn.close()
    return auth is not None

if not st.session_state['logged_in']:
    st.title("🦁 Edge Pro Analytics")
    with st.form("login"):
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if autenticar(u, p):
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Dados incorretos!")
    st.stop() # Trava o site aqui até logar

# --- SE CHEGOU AQUI, ESTÁ LOGADO! EXIBIR PAINEL ABAIXO ---
st.sidebar.success(f"Logado como: Operador")
if st.sidebar.button("Sair"):
    st.session_state['logged_in'] = False
    st.rerun()
st.set_page_config(page_title="Edge Pro Analytics", page_icon="🦁", layout="wide")

# CSS para visual profissional
st.markdown("""<style>
    .stMetric {background-color: #1E1E1E; padding: 15px; border-radius: 10px; border: 1px solid #333;}
    div[data-testid="stExpander"] {background-color: #0E1117; border: 1px solid #333; border-radius: 10px;}
</style>""", unsafe_allow_html=True)

def init_connection():
    db_url = os.getenv("DB_URL") or st.secrets.get("DB_URL")
    if not db_url:
        db_url = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
    return psycopg2.connect(db_url)

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = init_connection()
        # Buscamos a nova coluna match_date
        query = "SELECT * FROM analysis_logs ORDER BY match_date ASC LIMIT 100"
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            df.drop_duplicates(subset=['fixture_id'], keep='first', inplace=True)
        return df
    except:
        return pd.DataFrame()

st.sidebar.title("🦁 Filtros Edge Pro")
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

df = load_data()

# Título Principal
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
        
        # --- CORREÇÃO DE FUSO HORÁRIO BRASIL ---
        # 1. Converte o valor do banco para um objeto de tempo
        dt_obj = pd.to_datetime(row['match_date'])
        
        # 2. Garante que ele seja tratado como UTC e depois converte para São Paulo
        # Se o banco já vier com fuso, usamos tz_convert, se não, usamos tz_localize
        try:
            data_br = dt_obj.tz_localize('UTC').tz_convert('America/Sao_Paulo')
        except:
            data_br = dt_obj.tz_convert('America/Sao_Paulo')
            
        data_jogo = data_br.strftime('%d/%m %H:%M')
        # ---------------------------------------
        
        with st.expander(f"⏰ {data_jogo} | {row['fixture_name']} | EV: {row['valor_ev']:.2f}%", expanded=True):
            # ... resto do código ...
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
    st.warning("⏳ Aguardando o minerador processar novos jogos...")