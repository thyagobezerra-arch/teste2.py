import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA (VISUAL PRO)
# ==============================================================================
st.set_page_config(
    page_title="Edge Pro Analytics",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado para dar ar de "App Nativo"
st.markdown("""
    <style>
    .stMetric {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .stDataFrame {
        border: 1px solid #333;
        border-radius: 5px;
    }
    div[data-testid="stExpander"] {
        background-color: #0E1117;
        border: 1px solid #333;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# CONEXÃO COM O BANCO
# ==============================================================================
# Tenta pegar dos secrets do Streamlit Cloud, senão usa variável local (para testes)
def init_connection():
    db_url = os.getenv("DB_URL")
    if not db_url:
        try:
            return psycopg2.connect(st.secrets["DB_URL"])
        except:
            # Fallback para teste local se não tiver secrets
            return psycopg2.connect("postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres")
    return psycopg2.connect(db_url)

@st.cache_data(ttl=60) # Atualiza a cada 60 segundos
def load_data():
    try:
        conn = init_connection()
        # Pega os jogos mais recentes primeiro
        query = "SELECT * FROM analysis_logs ORDER BY created_at DESC LIMIT 100"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar no banco: {e}")
        return pd.DataFrame()

# ==============================================================================
# LAYOUT DO DASHBOARD
# ==============================================================================

# --- Sidebar (Filtros) ---
st.sidebar.title("🦁 Filtros Edge Pro")
st.sidebar.markdown("---")

df = load_data()

if not df.empty:
    # Filtro de Ligas (Extraindo do nome do jogo ou stats se possível, aqui simplificado)
    # Como salvamos tudo junto, vamos filtrar por texto
    filtro_texto = st.sidebar.text_input("Buscar Time ou Liga", "")
    
    # Filtro de EV Mínimo
    ev_minimo = st.sidebar.slider("Valor Esperado (EV) Mínimo %", 0, 50, 5)
    
    # Aplicando filtros
    df_filtrado = df[df['valor_ev'] >= ev_minimo]
    if filtro_texto:
        df_filtrado = df_filtrado[df_filtrado['fixture_name'].str.contains(filtro_texto, case=False)]
else:
    df_filtrado = pd.DataFrame()

# --- Cabeçalho ---
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.markdown("# 🦁")
with col_titulo:
    st.markdown("# Painel de Inteligência Esportiva")
    st.markdown("Monitoramento em Tempo Real de Oportunidades de Valor (+EV)")

st.markdown("---")

# --- KPIs (Indicadores Chave) ---
if not df.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Jogos Mapeados", len(df))
    with col2:
        oportunidades = len(df[df['valor_ev'] > 10])
        st.metric("Oportunidades Ouro (EV > 10%)", oportunidades, delta_color="normal")
    with col3:
        media_ev = df['valor_ev'].mean()
        st.metric("EV Médio do Mercado", f"{media_ev:.2f}%")
    with col4:
        st.metric("Última Atualização", df['created_at'].iloc[0].strftime('%H:%M'))

    st.markdown("---")
    
    # --- Lista de Jogos (Estilo Card) ---
    st.markdown("### 🎯 Oportunidades Encontradas")

    for index, row in df_filtrado.iterrows():
        # Cria um "Card" para cada jogo
        with st.expander(f"{row['fixture_name']}  |  EV: {row['valor_ev']:.2f}%", expanded=True):
            
            c1, c2, c3 = st.columns([1, 2, 1])
            
            # Coluna 1: O Velocímetro de Valor
            with c1:
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = row['valor_ev'],
                    title = {'text': "Valor Esperado (EV)"},
                    gauge = {
                        'axis': {'range': [None, 50]},
                        'bar': {'color': "#00ff00" if row['valor_ev'] > 15 else "#f1c40f"},
                        'steps': [
                            {'range': [0, 5], 'color': "gray"},
                            {'range': [5, 15], 'color': "#333"}],
                    }
                ))
                fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
                st.plotly_chart(fig, use_container_width=True)
            
            # Coluna 2: Detalhes Técnicos
            with c2:
                st.markdown("#### 📊 Análise Estatística")
                st.markdown(f"**Probabilidade Real:** `{row['probabilidade']:.1f}%`")
                st.markdown(f"**Odd Justa:** `{row['odd_justa']:.2f}` vs **Odd Mercado:** `{row['odd_mercado']:.2f}`")
                st.markdown(f"**Mercado Indicado:** `{row['mercado_tipo']}`")
                st.info(f"💡 {row['stats_resumo']}")
            
            # Coluna 3: Botão de Ação (Simulado)
            with c3:
                st.markdown("#### 🚀 Ação")
                st.markdown("Este jogo apresenta desajuste matemático.")
                st.button(f"Ver na Bet365 #{row['fixture_id']}")

else:
    st.warning("⏳ Aguardando dados do minerador... (Verifique se o GitHub Actions rodou)")