import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os
import uuid
from datetime import datetime, timedelta

# 1. CONFIGURAÇÃO DE PÁGINA "FULL SCREEN"
st.set_page_config(page_title="Edge Pro Analytics", page_icon="🦁", layout="wide")

# --- CSS PROFISSIONAL (ESTILO BETANO/FLASHSCORE) ---
st.markdown("""
    <style>
        /* Fundo Geral */
        .stApp {background-color: #121212;}
        
        /* Containers */
        .game-card {
            background-color: #1e1e1e;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #333;
            transition: transform 0.2s;
        }
        .game-card:hover {
            border-left: 4px solid #22c55e;
            transform: translateX(5px);
        }
        
        /* Tipografia */
        h1, h2, h3 {color: #ffffff !important; font-family: 'Roboto', sans-serif;}
        p, div {color: #b0b3b8;}
        .highlight-val {color: #22c55e; font-weight: bold;}
        .league-title {font-size: 11px; text-transform: uppercase; color: #888; letter-spacing: 1px;}
        
        /* Métricas */
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            text-align: center;
            background: #2b2b2b;
            padding: 10px;
            border-radius: 6px;
            margin-top: 10px;
        }
        .stat-item {font-size: 12px; color: #ccc;}
        .stat-value {font-size: 16px; font-weight: bold; color: white;}
        
        /* Badge Diamante */
        .diamond-badge {
            background-color: #22c55e;
            color: black;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
        }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXÃO DATABASE
def init_connection():
    db_url = os.getenv("DB_URL") or st.secrets.get("DB_URL")
    if not db_url:
        db_url = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
    return psycopg2.connect(db_url)

# 3. AUTENTICAÇÃO
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
    st.markdown("<br><br><h1 style='text-align: center;'>🦁 Edge Pro Analytics</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        with st.form("login_form"):
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("🔓 Entrar na Plataforma", use_container_width=True):
                if autenticar(u, p):
                    st.session_state['logged_in'] = True
                    st.rerun()
                else: st.error("Acesso negado.")
    st.stop()

# 4. CARREGAMENTO DE DADOS OTIMIZADO
@st.cache_data(ttl=60)
def load_data():
    try:
        conn = init_connection()
        # Busca apenas jogos futuros (Pré-Live)
        query = "SELECT * FROM analysis_logs WHERE match_date > NOW() ORDER BY valor_ev DESC LIMIT 100"
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            df.drop_duplicates(subset=['fixture_id'], keep='first', inplace=True)
        return df
    except: return pd.DataFrame()

# --- SIDEBAR (CONTROLE) ---
st.sidebar.markdown("### 🦁 Painel Controle")
filtro_diamante = st.sidebar.checkbox("💎 Apenas Oportunidades Diamante", value=False)
if st.sidebar.button("🔄 Atualizar Grade"): st.cache_data.clear(); st.rerun()
if st.sidebar.button("Sair"): st.session_state['logged_in'] = False; st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("Planos:\n\n🔹 **Básico**: Sinais + Telegram\n\n🔸 **Avançado**: Comunidade + Lives")

# --- MAIN FEED ---
df = load_data()

st.title("🦁 Painel de Oportunidades")

if not df.empty:
    # Filtro Lógico
    if filtro_diamante:
        df = df[df['valor_ev'] >= 65] # Só mostra altíssimo valor
        st.caption("💎 Exibindo apenas jogos de Alta Convicção (EV > 65)")
    else:
        st.caption(f"📅 Grade Completa: {len(df)} jogos analisados nas próximas 48h")

    for i, row in df.iterrows():
        # Parsing Robusto de Dados (O segredo do Dashboard)
        try:
            # O formato esperado é: "Gols:2.5|+1.5:80%|CantosProj:9.5|CardProj:4.5|Chutes:24|WinH:60%|WinA:20%"
            dados = {}
            parts = row['stats_resumo'].split('|')
            for p in parts:
                k, v = p.split(':')
                dados[k.strip()] = v.strip()
            
            # Extrai valores com segurança
            media_gols = dados.get('Gols', '-')
            prob_over15 = dados.get('+1.5', '-')
            cantos_proj = dados.get('CantosProj', '-')
            cards_proj = dados.get('CardProj', '-')
            chutes_total = dados.get('Chutes', '-')
            win_h = dados.get('WinH', '0%')
            win_a = dados.get('WinA', '0%')
            
        except:
            # Fallback se o dado vier quebrado
            media_gols, prob_over15, cantos_proj, cards_proj, chutes_total, win_h = "-", "-", "-", "-", "-", "-"

        # Separa Liga e Times
        try:
            if '#' in row['fixture_name']:
                liga, times = row['fixture_name'].split('#')
            else:
                liga, times = "FUTEBOL", row['fixture_name']
        except: liga, times = "FUTEBOL", row['fixture_name']

        # Fuso Horário
        match_time = pd.to_datetime(row['match_date']) - timedelta(hours=3)
        hora_jogo = match_time.strftime('%H:%M')
        dia_jogo = match_time.strftime('%d/%m')

        # --- COMPONENTE VISUAL (CARD) ---
        with st.container():
            # Cabeçalho do Card
            col_liga, col_ev = st.columns([3, 1])
            with col_liga:
                if row['valor_ev'] > 70:
                    st.markdown(f"<span class='diamond-badge'>💎 DIAMANTE</span> <span class='league-title'>{liga}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span class='league-title'>{liga}</span>", unsafe_allow_html=True)
                st.markdown(f"### {times}")
                st.caption(f"📅 {dia_jogo} às {hora_jogo}")

            with col_ev:
                # Velocímetro Minimalista
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=row['valor_ev'],
                    number={'suffix': "", 'font': {'size': 20, 'color': "white"}},
                    gauge={'axis': {'range': [None, 100], 'visible': False}, 
                           'bar': {'color': "#22c55e" if row['valor_ev'] > 65 else "#f59e0b"}, 
                           'bgcolor': "#333"}
                ))
                fig.update_layout(height=80, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, key=f"g_{i}")

            # Grid de Estatísticas (O "Painel da NASA")
            st.markdown(f"""
                <div class='stat-grid'>
                    <div>
                        <div class='stat-item'>GOLS (Média)</div>
                        <div class='stat-value' style='color:#60a5fa'>{media_gols}</div>
                    </div>
                    <div>
                        <div class='stat-item'>ESCANTES</div>
                        <div class='stat-value' style='color:#facc15'>~{cantos_proj}</div>
                    </div>
                    <div>
                        <div class='stat-item'>CARTÕES</div>
                        <div class='stat-value' style='color:#f87171'>~{cards_proj}</div>
                    </div>
                    <div>
                        <div class='stat-item'>FINALIZAÇÕES</div>
                        <div class='stat-value'>{chutes_total}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Probabilidades de Vitória (Moneyline)
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Casa Vence", win_h)
            with c2: st.metric("Empate", "---") # Empate é difícil calcular em Poisson simples, deixamos neutro
            with c3: st.metric("Visitante", win_a)
            
            st.button(f"📊 Ver Análise Detalhada ({times})", key=f"btn_{i}", use_container_width=True)
            st.markdown("---")

else:
    st.info("🔎 Carregando a Inteligência Artificial... Se demorar, clique em 'Atualizar Grade'.")