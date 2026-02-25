import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import re

# --- CONFIGURAÇÃO DA PÁGINA (MOBILE FIRST) ---
st.set_page_config(page_title="Edge Pro Live", page_icon="🦁", layout="wide", initial_sidebar_state="collapsed")

# --- CSS AVANÇADO (ESTILO BET365 / GLASSMORPHISM) ---
st.markdown("""
    <style>
    /* Importando Fonte Moderna */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        background-color: #0e1117; 
        color: #e0e0e0;
    }

    /* Esconde menu padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* CABEÇALHO PERSONALIZADO */
    .custom-header {
        background: linear-gradient(90deg, #1c1c1c 0%, #000000 100%);
        padding: 15px;
        border-bottom: 2px solid #00ffb7;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-radius: 0 0 15px 15px;
    }
    .logo-text { font-size: 24px; font-weight: bold; color: #fff; }
    .logo-icon { font-size: 24px; margin-right: 10px; }

    /* CARD DE JOGO (GLASSMORPHISM) */
    .game-card {
        background: rgba(30, 30, 30, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        transition: transform 0.2s;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .game-card:hover {
        transform: translateY(-2px);
        border-color: #00ffb7;
    }
    
    /* BADGES E ETIQUETAS */
    .badge-live {
        background-color: #ef4444; color: white; padding: 2px 8px; 
        border-radius: 4px; font-size: 10px; font-weight: bold; letter-spacing: 1px;
    }
    .badge-league {
        color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .game-title {
        font-size: 18px; font-weight: 700; color: #ffffff; margin: 10px 0;
    }
    .money-badge {
        background: rgba(0, 255, 183, 0.15);
        color: #00ffb7;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        border: 1px solid rgba(0, 255, 183, 0.3);
        display: inline-block;
    }

    /* GRID DE ESTATÍSTICAS */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(60px, 1fr));
        gap: 8px;
        margin-top: 15px;
        background: rgba(0,0,0,0.3);
        padding: 10px;
        border-radius: 12px;
    }
    .stat-item { text-align: center; }
    .stat-label { font-size: 9px; color: #64748b; text-transform: uppercase; }
    .stat-val { font-size: 14px; font-weight: bold; color: #e2e8f0; }
    
    /* Tabs Customizadas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap;
        background-color: #1c1c1c; border-radius: 8px; color: white;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00ffb7 !important; color: black !important;
    }
    </style>
    
    <div class="custom-header">
        <div>
            <span class="logo-icon">🦁</span>
            <span class="logo-text">EDGE PRO</span>
        </div>
        <div style="font-size: 12px; color: #888;">Live v3.0</div>
    </div>
    """, unsafe_allow_html=True)

# --- CONEXÃO SEGURA (PARA NUVEM) ---
try:
    # Na nuvem, ele vai pegar daqui automaticamente
    DB_URL = st.secrets["DB_URL"]
except:
    # No seu PC, coloque o link aqui para testar, MAS APAGUE ANTES DE SUBIR PRO GITHUB
    DB_URL = "COLE_SEU_LINK_AQUI_PARA_TESTE_LOCAL"

# --- FUNÇÕES (Mantidas iguais, focando na performance) ---
def criar_mini_donut(valor, cor):
    if valor is None: return None
    fig = go.Figure(go.Pie(values=[valor, 100-valor], hole=0.8, marker_colors=[cor, '#333'], textinfo='none', hoverinfo='none'))
    fig.add_annotation(text=f"{int(valor)}", showarrow=False, font=dict(size=10, color=cor)) # Sem % pra caber melhor
    fig.update_layout(showlegend=False, height=45, margin={'t':0,'b':0,'l':0,'r':0}, paper_bgcolor='rgba(0,0,0,0)')
    return fig

def processar_stats(texto):
    d = {"fav": "", "ov15": 0, "ov25": 0, "und25": 0, "btts": 0, "cantos": 0, "chutes": 0, "cartoes": 0, "ia": ""}
    if not texto: return d
    try:
        tags = {
            "ov15": r'\[OV15\](.*?)\[/OV15\]', "ov25": r'\[OV25\](.*?)\[/OV25\]',
            "und25": r'\[UND25\](.*?)\[/UND25\]', "btts": r'\[BTTS\](.*?)\[/BTTS\]',
            "cantos": r'\[CANTOS\](.*?)\[/CANTOS\]', "chutes": r'\[CHUTES\](.*?)\[/CHUTES\]',
            "cartoes": r'\[CARTOES\](.*?)\[/CARTOES\]'
        }
        for k, v in tags.items():
            match = re.search(v, texto)
            if match: d[k] = float(match.group(1))
        m_fav = re.search(r'Favorito: \*\*(.*?)\*\*', texto)
        if m_fav: d['fav'] = m_fav.group(1)
        m_ia = re.search(r'IA: (.*)', texto)
        if m_ia: d['ia'] = m_ia.group(1)
    except: pass
    return d

@st.cache_data(ttl=10)
def carregar_dados():
    try:
        if "COLE_SEU" in DB_URL: return pd.DataFrame(), "⚠️ Configure os Secrets na Nuvem!"
        conn = psycopg2.connect(DB_URL)
        df = pd.read_sql("SELECT * FROM analysis_logs WHERE mercado_tipo = 'Gols' ORDER BY created_at DESC LIMIT 60", conn)
        conn.close()
        return df, "OK"
    except Exception as e: return pd.DataFrame(), str(e)

# --- RENDERIZAÇÃO DO CARD (HTML PURO + STYLED) ---
def renderizar_card(row, banca_val):
    s = processar_stats(row['stats_resumo'])
    if s['ov15'] == 0: return

    partes = row['fixture_name'].split('|')
    liga = partes[0].replace("⭐", "").replace("⚽", "").strip()
    jogo = partes[1].strip() if len(partes) > 1 else row['fixture_name']
    stake = banca_val * (0.02 if row['valor_ev'] > 15 else 0.01)

    # LAYOUT DO CARD
    with st.container():
        st.markdown(f"""
        <div class="game-card">
            <div style="display:flex; justify-content:space-between;">
                <span class="badge-league">🏆 {liga}</span>
                <span class="badge-live">LIVE</span>
            </div>
            <div class="game-title">{jogo}</div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span style="font-size:12px; color:#888;">🔥 {s['fav']}</span>
                <div class="money-badge">R$ {stake:.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Colunas de Gráficos (Streamlit Columns dentro do Container HTML)
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: 
            st.markdown("<div class='stat-item'><div class='stat-label'>Over 1.5</div>", unsafe_allow_html=True)
            st.plotly_chart(criar_mini_donut(s['ov15'], "#facc15"), use_container_width=True, key=f"k1{row['id']}")
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div class='stat-item'><div class='stat-label'>Over 2.5</div>", unsafe_allow_html=True)
            st.plotly_chart(criar_mini_donut(s['ov25'], "#22c55e"), use_container_width=True, key=f"k2{row['id']}")
            st.markdown("</div>", unsafe_allow_html=True)
        with c3:
            st.markdown("<div class='stat-item'><div class='stat-label'>BTTS</div>", unsafe_allow_html=True)
            st.plotly_chart(criar_mini_donut(s['btts'], "#3b82f6"), use_container_width=True, key=f"k3{row['id']}")
            st.markdown("</div>", unsafe_allow_html=True)
        with c4:
             st.markdown(f"<div class='stat-item'><div class='stat-label'>Under 2.5</div><div class='stat-val' style='color:#ef4444'>{int(s['und25'])}%</div></div>", unsafe_allow_html=True)
        with c5:
             st.markdown(f"<div class='stat-item'><div class='stat-label'>Cantos</div><div class='stat-val'>+{s['cantos']}</div></div>", unsafe_allow_html=True)
        with c6:
             st.markdown(f"<div class='stat-item'><div class='stat-label'>Cartões</div><div class='stat-val'>{s['cartoes']}</div></div>", unsafe_allow_html=True)
        with c7:
             st.markdown(f"<div class='stat-item'><div class='stat-label'>Chutes</div><div class='stat-val'>{s['chutes']}</div></div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# --- CORPO PRINCIPAL ---
df, status = carregar_dados()

# Sidebar Minimalista
st.sidebar.header("⚙️ Banca")
banca = st.sidebar.number_input("Valor Total", value=1000.0, step=50.0, label_visibility="collapsed")

if status == "OK" and not df.empty:
    LIGAS_ELITE = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Brasileirão", "Champions League", "Libertadores"]
    df['Liga_Limpa'] = df['fixture_name'].apply(lambda x: x.split('|')[0].replace("⭐", "").replace("⚽", "").strip())
    
    # Abas com Ícones
    tab1, tab2 = st.tabs(["⭐ ELITE VIP", "🌍 MUNDO"])
    
    with tab1:
        elite = df[df['Liga_Limpa'].apply(lambda x: any(v in x for v in LIGAS_ELITE))]
        if not elite.empty:
            for _, row in elite.iterrows(): renderizar_card(row, banca)
        else: st.info("Sem jogos da Elite no momento.")
            
    with tab2:
        mundo = df[~df['Liga_Limpa'].apply(lambda x: any(v in x for v in LIGAS_ELITE))]
        if not mundo.empty:
            for _, row in mundo.iterrows(): renderizar_card(row, banca)
        else: st.info("Aguardando jogos...")
else:
    st.error(status)