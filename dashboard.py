import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os
import uuid
from datetime import datetime, timedelta
import pytz

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="Edge Pro Analytics", page_icon="🦁", layout="wide")

# 2. CONEXÃO
def init_connection():
    db_url = os.getenv("DB_URL") or st.secrets.get("DB_URL")
    if not db_url:
        db_url = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
    return psycopg2.connect(db_url)

# 3. LOGIN OTIMIZADO
def autenticar(user, pwd):
    try:
        conn = init_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s AND password = %s", (user, pwd))
        auth = cur.fetchone()
        conn.close()
        return auth is not None
    except: return False

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>🦁 Edge Pro Analytics</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("🔓 Acessar Painel VIP", use_container_width=True):
            if autenticar(u, p):
                st.session_state['logged_in'] = True
                st.rerun()
            else: st.error("Acesso negado.")
    st.stop()

# --- DASHBOARD DE ANTECIPAÇÃO ---

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = init_connection()
        # FILTRO DE OURO: Só traz jogos DAQUI PARA FRENTE (UTC)
        query = """
            SELECT * FROM analysis_logs 
            WHERE match_date > NOW() 
            ORDER BY match_date ASC 
            LIMIT 100
        """
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            df.drop_duplicates(subset=['fixture_id'], keep='first', inplace=True)
        return df
    except: return pd.DataFrame()

# Menu
st.sidebar.title("🦁 Painel VIP")
if st.sidebar.button("🔄 Atualizar Grade"): st.cache_data.clear(); st.rerun()
if st.sidebar.button("Sair"): st.session_state['logged_in'] = False; st.rerun()

df = load_data()

st.markdown("# 🦁 Próximas Oportunidades (48h)")
st.markdown("---")

if not df.empty:
    ev_min = st.sidebar.slider("EV Mínimo", 0, 50, 10)
    df = df[df['valor_ev'] >= ev_min]
    
    for i, row in df.iterrows():
        chave = str(uuid.uuid4())
        
        # Converte UTC para João Pessoa (-3h)
        match_time = pd.to_datetime(row['match_date'])
        br_time = match_time - timedelta(hours=3)
        
        # Filtro Visual Extra: Se já passou do horário, não mostra (redundância de segurança)
        if br_time < (datetime.now() - timedelta(hours=3)): continue
        
        str_data = br_time.strftime('%d/%m %H:%M')
        
        # Tratamento de Strings do Resumo
        try:
            parts = row['stats_resumo'].split('|')
            media_gols = parts[0].split(':')[1].strip()
            prob_over_15 = parts[1].split(':')[1].strip()
        except:
            media_gols, prob_over_15 = "N/A", "N/A"

        with st.expander(f"⏰ {str_data} | {row['fixture_name']}", expanded=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=row['valor_ev'],
                    title={'text': "EV Score", 'font': {'size': 15}},
                    gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "gold"}}
                ))
                fig.update_layout(height=140, margin=dict(t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
                st.plotly_chart(fig, use_container_width=True, key=f"g_{chave}")
            
            with c2:
                st.markdown("##### 📊 Raio-X da Partida")
                st.info(f"⚽ **Gols:** Média {media_gols} | +1.5: {prob_over_15} | +2.5: {row['gols_ev']:.0f}%")
                st.warning(f"🚩 **Cantos:** +9.5: {row['cantos_ev']:.0f}% de chance")
            
            with c3:
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("📲 Alertar Grupo", key=f"b_{chave}", use_container_width=True)

else:
    st.info("🔎 Buscando as melhores oportunidades para as próximas 48h...")