import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import re 

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Edge Pro Stats", page_icon="🦁", layout="wide")

try:
    DB_URL = st.secrets["DB_URL"]
except:
    DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

# --- CSS DARK MODE PROFISSIONAL ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .game-card {
        background-color: #1e1e1e;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #00ffb7;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    h1, h2, h3 { color: white !important; font-family: sans-serif; }
    p, span, div { color: #b0b0b0; }
    .stat-label { font-size: 12px; color: #888; text-transform: uppercase; }
    .stat-value { font-size: 18px; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES GRÁFICAS (DONUT CHART) ---
def criar_donut(valor, titulo, cor):
    if valor == 0: return None
    fig = go.Figure(go.Pie(
        values=[valor, 100-valor],
        hole=0.75,
        marker_colors=[cor, '#2a2a2a'],
        textinfo='none',
        hoverinfo='none'
    ))
    # Texto Central
    fig.add_annotation(text=f"{int(valor)}%", showarrow=False, font=dict(size=16, color=cor, family="Arial Black"))
    fig.add_annotation(text=titulo, showarrow=False, font=dict(size=10, color='#888'), y=0.15)
    
    fig.update_layout(
        showlegend=False, 
        height=120, 
        margin={'t':0,'b':0,'l':0,'r':0}, 
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- EXTRAÇÃO DE DADOS INTELIGENTE ---
def processar_stats(texto_stats):
    """Lê o texto salvo pelo robô e extrai os números e nomes"""
    dados = {
        "fav": "Indefinido",
        "ov15": 0.0,
        "ov25": 0.0,
        "ia": "Sem análise"
    }
    if not texto_stats: return dados

    try:
        # Tenta achar Over 1.5
        match_15 = re.search(r'\[OV15\](.*?)\[/OV15\]', texto_stats)
        if match_15: dados['ov15'] = float(match_15.group(1))

        # Tenta achar Over 2.5
        match_25 = re.search(r'\[OV25\](.*?)\[/OV25\]', texto_stats)
        if match_25: dados['ov25'] = float(match_25.group(1))

        # Tenta achar o Nome do Favorito
        match_fav = re.search(r'Favorito: \*\*(.*?)\*\*', texto_stats)
        if match_fav: dados['fav'] = match_fav.group(1)
        
        # Tenta achar o conselho da IA
        match_ia = re.search(r'IA: (.*)', texto_stats)
        if match_ia: dados['ia'] = match_ia.group(1)

    except:
        pass
    
    return dados

# --- CARREGAMENTO DO BANCO ---
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        conn = psycopg2.connect(DB_URL)
        # Pega os 50 jogos mais recentes de GOLS
        query = "SELECT * FROM analysis_logs WHERE mercado_tipo = 'Gols' ORDER BY created_at DESC LIMIT 50"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

# --- INTERFACE PRINCIPAL ---
st.title("⚽ Painel Profissional de Gols")
st.markdown("Monitoramento de Over 1.5 e 2.5 com Cálculo de Poisson")

df = carregar_dados()

if not df.empty:
    for _, row in df.iterrows():
        # Tratamento do Nome
        partes = row['fixture_name'].split('|')
        liga = partes[0].strip() if len(partes) > 1 else "Liga"
        jogo = partes[1].strip() if len(partes) > 1 else row['fixture_name']
        
        # Processa as estatísticas
        stats = processar_stats(row['stats_resumo'])
        
        # --- RENDERIZA O CARD ---
        with st.container():
            st.markdown(f"""<div class="game-card">""", unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                st.caption(f"🏆 {liga}")
                st.markdown(f"### {jogo}")
                if stats['fav'] != "Indefinido":
                    st.markdown(f"🔥 Favorito: **{stats['fav']}**")
                else:
                    st.markdown(f"⚖️ Jogo Equilibrado")

            with col2:
                # Exibe a análise em texto da IA
                st.caption("🤖 Análise da IA")
                st.info(stats['ia'] if len(stats['ia']) > 2 else "Análise básica indisponível")

            with col3:
                # Gráfico Over 1.5
                if stats['ov15'] > 0:
                    st.plotly_chart(criar_donut(stats['ov15'], "Over 1.5", "#ffcc00"), use_container_width=True, key=f"d15_{row['id']}")
                else:
                    st.markdown("---")
            
            with col4:
                # Gráfico Over 2.5
                cor_25 = "#00ffb7" if stats['ov25'] > 60 else "#ff4b4b"
                if stats['ov25'] > 0:
                    st.plotly_chart(criar_donut(stats['ov25'], "Over 2.5", cor_25), use_container_width=True, key=f"d25_{row['id']}")
                else:
                    st.markdown("---")

            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.error("Erro de conexão ou tabela vazia. Tente recarregar.")