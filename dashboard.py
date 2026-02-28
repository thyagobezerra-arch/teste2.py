import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os
import uuid
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Edge Pro Analytics", page_icon="🦁", layout="wide")

def init_connection():
    db_url = os.getenv("DB_URL") or st.secrets.get("DB_URL")
    if not db_url:
        db_url = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
    return psycopg2.connect(db_url)

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

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = init_connection()
        query = "SELECT * FROM analysis_logs WHERE match_date > NOW() ORDER BY match_date ASC LIMIT 100"
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            df.drop_duplicates(subset=['fixture_id'], keep='first', inplace=True)
        return df
    except: return pd.DataFrame()

# Menu Lateral
st.sidebar.title("🦁 Painel VIP")
if st.sidebar.button("🔄 Atualizar Grade"): st.cache_data.clear(); st.rerun()
if st.sidebar.button("Sair"): st.session_state['logged_in'] = False; st.rerun()

df = load_data()

st.markdown("# 🦁 Grade de Oportunidades")
st.markdown("---")

if not df.empty:
    ev_min = st.sidebar.slider("Filtrar por EV Score", 0, 50, 10)
    df = df[df['valor_ev'] >= ev_min]
    
    st.sidebar.write(f"📊 **{len(df)}** jogos encontrados.")

    for i, row in df.iterrows():
        chave = str(uuid.uuid4())
        
        # Ajuste de Fuso e Hora
        match_time = pd.to_datetime(row['match_date'])
        br_time = match_time - timedelta(hours=3)
        if br_time < (datetime.now() - timedelta(hours=3)): continue
        str_data = br_time.strftime('%H:%M')
        dia_semana = br_time.strftime('%d/%m')

        # SEPARAÇÃO INTELIGENTE: Liga vs Times
        # O robô agora salva como "LIGA # TIME A x TIME B"
        try:
            if '#' in row['fixture_name']:
                liga_nome, times_nome = row['fixture_name'].split('#')
            else:
                liga_nome = "🏆 Campeonato"
                times_nome = row['fixture_name']
        except:
            liga_nome = "Futebol"
            times_nome = row['fixture_name']

        # Parsing de Stats
        try:
            parts = row['stats_resumo'].split('|')
            media_gols = parts[0].split(':')[1].strip()
            prob_over_15 = parts[1].split(':')[1].strip()
        except: media_gols, prob_over_15 = "-", "-"

        # CARD VISUAL PROFISSIONAL
        # O título agora mostra: 🏆 LIGA  |  ⏰ HORA  |  TIMES
        titulo_card = f"🏆 **{liga_nome.strip()}** |  ⏰ {dia_semana} às {str_data}  |  ⚽ {times_nome.strip()}"
        
        with st.expander(titulo_card, expanded=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=row['valor_ev'],
                    title={'text': "EV Score", 'font': {'size': 15}},
                    gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#00ff00" if row['valor_ev'] > 75 else "gold"}}
                ))
                fig.update_layout(height=130, margin=dict(t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
                st.plotly_chart(fig, use_container_width=True, key=f"g_{chave}")
            
            with c2:
                st.markdown(f"### {times_nome.strip()}")
                st.info(f"📊 **Estatísticas:** Média de Gols {media_gols} | +1.5 Gols: {prob_over_15}")
                st.warning(f"⛳ **Cantos:** +9.5 projetado com {row['cantos_ev']:.0f}% de chance")
            
            with c3:
                st.markdown("<br>", unsafe_allow_html=True)
                bet_link = "https://www.bet365.com"
                st.markdown(f"""<a href="{bet_link}" target="_blank"><button style="width:100%; padding:10px; background-color:#1e3a8a; color:white; border:none; border-radius:5px; cursor:pointer;">💰 Abrir na Bet365</button></a>""", unsafe_allow_html=True)

else:
    st.info("🔎 O Robô está varrendo as ligas... aguarde a próxima sincronização.")