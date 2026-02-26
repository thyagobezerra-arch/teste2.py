import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Edge Pro Analytics",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado
st.markdown("""
    <style>
    .stMetric {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
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
def init_connection():
    db_url = os.getenv("DB_URL")
    if not db_url:
        try:
            return psycopg2.connect(st.secrets["DB_URL"])
        except:
            return psycopg2.connect("postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres")
    return psycopg2.connect(db_url)

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = init_connection()
        query = "SELECT * FROM analysis_logs ORDER BY created_at DESC LIMIT 100"
        df = pd.read_sql(query, conn)
        conn.close()
        
        # --- CORREÇÃO 1: REMOVE DUPLICATAS ---
        # Mantém apenas a primeira ocorrência de cada jogo (fixture_id), eliminando repetições do teste
        if not df.empty:
            df.drop_duplicates(subset=['fixture_id'], keep='first', inplace=True)
            
        return df
    except Exception as e:
        st.error(f"Erro ao conectar no banco: {e}")
        return pd.DataFrame()

# ==============================================================================
# LAYOUT DO DASHBOARD
# ==============================================================================

st.sidebar.title("🦁 Filtros Edge Pro")
st.sidebar.markdown("---")

df = load_data()

if not df.empty:
    filtro_texto = st.sidebar.text_input("Buscar Time ou Liga", "")
    ev_minimo = st.sidebar.slider("Valor Esperado (EV) Mínimo %", 0, 50, 5)
    
    df_filtrado = df[df['valor_ev'] >= ev_minimo]
    if filtro_texto:
        df_filtrado = df_filtrado[df_filtrado['fixture_name'].str.contains(filtro_texto, case=False)]
else:
    df_filtrado = pd.DataFrame()

col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.markdown("# 🦁")
with col_titulo:
    st.markdown("# Painel de Inteligência Esportiva")
    st.markdown("Monitoramento em Tempo Real de Oportunidades de Valor (+EV)")

st.markdown("---")

if not df.empty:
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Jogos Únicos", len(df_filtrado))
    with col2: st.metric("Oportunidades Ouro", len(df_filtrado[df_filtrado['valor_ev'] > 10]))
    with col3: st.metric("EV Médio", f"{df_filtrado['valor_ev'].mean():.2f}%")
    with col4: st.metric("Última Atualização", df['created_at'].iloc[0].strftime('%H:%M'))

    st.markdown("---")
    
    st.markdown("### 🎯 Oportunidades Encontradas")

    for index, row in df_filtrado.iterrows():
        # Card Expansível
        with st.expander(f"{row['fixture_name']}  |  EV: {row['valor_ev']:.2f}%", expanded=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            
            with c1:
                # Gráfico Velocímetro
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
            
            with c2:
                st.markdown("#### 📊 Análise Estatística")
                st.markdown(f"**Probabilidade Real:** `{row['probabilidade']:.1f}%`")
                st.markdown(f"**Odd Justa:** `{row['odd_justa']:.2f}` vs **Odd Mercado:** `{row['odd_mercado']:.2f}`")
                st.markdown(f"**Mercado Indicado:** `{row['mercado_tipo']}`")
                st.info(f"💡 {row['stats_resumo']}")
            
            with c3:
                st.markdown("#### 🚀 Ação")
                st.markdown("Este jogo apresenta desajuste matemático.")
                # --- CORREÇÃO 2: KEY ÚNICA ---
                # O parâmetro key=... garante que o Streamlit saiba diferenciar os botões
                st.button(f"Ver na Bet365 #{row['fixture_id']}", key=f"btn_{row['id']}_{index}")

else:
    st.warning("⏳ Aguardando dados... Verifique se o GitHub Actions rodou.")