import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os
import uuid

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
        
        # Formatação de Data e Hora
        data_jogo = pd.to_datetime(row['match_date']).strftime('%d/%m %H:%M')
        
        with st.expander(f"⏰ {data_jogo} | {row['fixture_name']} | EV: {row['valor_ev']:.2f}%", expanded=True):
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