import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os
import uuid
from datetime import datetime, timedelta

st.set_page_config(page_title="Edge Pro Analytics", page_icon="🦁", layout="wide")

# --- CSS PROFISSIONAL (DARK MODE PREMIUM) ---
st.markdown("""
    <style>
        .stApp {background-color: #0b0c10;}
        .card-container {
            background-color: #1f2833;
            padding: 20px;
            border-radius: 12px;
            border-left: 5px solid #66fcf1;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .stat-box {
            background-color: #2c353f;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            color: #c5c6c7;
        }
        .big-number {
            font-size: 24px;
            font-weight: bold;
            color: #66fcf1;
        }
        .league-tag {
            font-size: 12px;
            color: #45a29e;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        h1, h2, h3 {color: white !important;}
        p {color: #c5c6c7;}
    </style>
""", unsafe_allow_html=True)

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
    st.markdown("<h1 style='text-align: center; color: white;'>🦁 Edge Pro Analytics</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("🔓 Acessar Plataforma", use_container_width=True):
            if autenticar(u, p):
                st.session_state['logged_in'] = True
                st.rerun()
            else: st.error("Dados inválidos.")
    st.stop()

@st.cache_data(ttl=30)
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

# Menu
st.sidebar.markdown("## 🦁 Painel Controle")
if st.sidebar.button("🔄 Atualizar Dados"): st.cache_data.clear(); st.rerun()
if st.sidebar.button("Sair"): st.session_state['logged_in'] = False; st.rerun()

df = load_data()

st.markdown("# 🦁 Oportunidades Premium")
st.markdown("---")

if not df.empty:
    ev_min = st.sidebar.slider("Filtrar Probabilidade Global (%)", 0, 100, 50)
    df = df[df['valor_ev'] >= ev_min]
    
    for i, row in df.iterrows():
        # Parsing dos dados ricos
        try:
            parts = row['stats_resumo'].split('|')
            media_gols = parts[0].split(':')[1].strip()
            prob_over_15 = parts[1].split(':')[1].strip()
            exp_cantos_val = parts[3].split(':')[1].strip()
        except:
            media_gols = "N/A"
            prob_over_15 = "N/A"
            exp_cantos_val = "N/A"

        # Título e Liga
        if '#' in row['fixture_name']:
            liga, jogo = row['fixture_name'].split('#')
        else:
            liga, jogo = "CAMPEONATO", row['fixture_name']
        
        match_time = pd.to_datetime(row['match_date']) - timedelta(hours=3)
        hora = match_time.strftime('%H:%M')
        
        # --- LAYOUT DO CARD PROFISSIONAL ---
        with st.container():
            # Cabeçalho do Card
            st.markdown(f"""
                <div class='card-container'>
                    <div class='league-tag'>{liga.strip()} • ⏰ {hora}</div>
                    <h3 style='margin: 5px 0 15px 0;'>{jogo.strip()}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                # Velocímetro Pequeno
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=row['valor_ev'],
                    number={'suffix': "%", 'font': {'size': 20, 'color': "white"}},
                    gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#66fcf1"}, 'bgcolor': "#1f2833"}
                ))
                fig.update_layout(height=100, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, key=f"g_{i}")
                st.caption("Força do Jogo")
            
            with c2:
                st.markdown(f"""
                    <div class='stat-box'>
                        <div style='font-size:12px'>GOLS ESPERADOS</div>
                        <div class='big-number'>{media_gols}</div>
                        <div style='font-size:10px; color:#45a29e'>+1.5 em {prob_over_15}</div>
                    </div>
                """, unsafe_allow_html=True)

            with c3:
                # Lógica de cor para cantos (Se > 50% fica verde, senão amarelo)
                cor_cantos = "#66fcf1" if row['cantos_ev'] > 50 else "#f0ad4e"
                st.markdown(f"""
                    <div class='stat-box'>
                        <div style='font-size:12px'>CANTOS PROJ.</div>
                        <div class='big-number' style='color:{cor_cantos}'>~{exp_cantos_val}</div>
                        <div style='font-size:10px; color:{cor_cantos}'>+9.5 em {row['cantos_ev']:.0f}%</div>
                    </div>
                """, unsafe_allow_html=True)
                
            with c4:
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("Ver na Bet365 ↗", key=f"btn_{i}", use_container_width=True)

else:
    st.info("O Minerador está calculando as projeções matemáticas...")