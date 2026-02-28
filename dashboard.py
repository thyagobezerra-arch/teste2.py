import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import os
import uuid
from datetime import timedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Edge Pro Analytics", page_icon="🦁", layout="wide")

# 2. FUNÇÃO DE CONEXÃO
def init_connection():
    db_url = os.getenv("DB_URL") or st.secrets.get("DB_URL")
    if not db_url:
        db_url = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
    return psycopg2.connect(db_url)

# 3. SISTEMA DE LOGIN COM FEEDBACK VISUAL
def autenticar(user, pwd):
    try:
        conn = init_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s AND password = %s", (user, pwd))
        auth = cur.fetchone()
        conn.close()
        return auth is not None
    except Exception as e:
        st.error(f"Erro técnico de conexão: {e}")
        return False

# Inicializa a sessão
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- TELA DE ACESSO (TRAVA ATÉ LOGAR) ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>🦁 Edge Pro Analytics</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        u = st.text_input("Usuário", placeholder="Seu nome de usuário")
        p = st.text_input("Senha", type="password", placeholder="Sua senha secreta")
        
        # O botão agora é mais direto para evitar travamentos
        if st.button("🔓 Acessar Sistema", use_container_width=True):
            if autenticar(u, p):
                st.session_state['logged_in'] = True
                st.success("✅ Acesso autorizado! Abrindo painel...")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos. Verifique os dados.")
    st.stop()

# --- DAQUI PARA BAIXO: SÓ CARREGA DEPOIS DO LOGIN ---

@st.cache_data(ttl=1) # Cache de apenas 1 segundo para garantir dados novos
def load_data():
    try:
        conn = init_connection()
        # Mostramos tudo o que o minerador salvou nas últimas 24h
        query = "SELECT * FROM analysis_logs ORDER BY match_date ASC LIMIT 100"
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            df.drop_duplicates(subset=['fixture_id'], keep='first', inplace=True)
        return df
    except:
        return pd.DataFrame()

# Menu Lateral de Suporte
st.sidebar.title("🦁 Painel VIP")
if st.sidebar.button("🔄 Atualizar Grade"):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("Sair (Logout)"):
    st.session_state['logged_in'] = False
    st.rerun()

# CARREGAMENTO DOS DADOS
df = load_data()

st.markdown("# 🦁 Inteligência Esportiva")
st.markdown("---")

if not df.empty:
    ev_minimo = st.sidebar.slider("Filtro EV % Mínimo", 0, 50, 10)
    df_filtrado = df[df['valor_ev'] >= ev_minimo]
    
    st.sidebar.info(f"Monitorando {len(df_filtrado)} jogos agora.")

    # ... (Mantenha o início do seu arquivo igual até chegar no loop 'for i, row in df_filtrado.iterrows():')

    for i, row in df_filtrado.iterrows():
        chave = str(uuid.uuid4())
        
        # Ajuste Fuso
        horario_br = pd.to_datetime(row['match_date']) - timedelta(hours=3)
        data_formatada = horario_br.strftime('%d/%m %H:%M')
        
        # Extraindo dados do texto resumo (Gambiarra inteligente para não mudar o banco agora)
        # O resumo vem assim: "Média Gols: 2.80 | Over 1.5: 85% | Over 2.5: 65% | Exp. Cantos: ~10.2"
        try:
            stats_text = row['stats_resumo']
            parts = stats_text.split('|')
            media_gols = parts[0].split(':')[1].strip()
            prob_over_15 = parts[1].split(':')[1].strip()
            media_cantos = parts[3].split(':')[1].strip()
        except:
            media_gols = "-"
            prob_over_15 = "-"
            media_cantos = "-"

        with st.expander(f"⏰ {data_formatada} | {row['fixture_name']}", expanded=True):
            
            c1, c2, c3 = st.columns([1, 2, 1])
            
            with c1:
                # VELOCÍMETRO (EV GERAL)
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number", value = row['valor_ev'],
                    title = {'text': "Potencial (EV)", 'font': {'size': 16}},
                    gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#00ff00" if row['valor_ev'] > 70 else "gold"}}
                ))
                fig.update_layout(height=160, margin=dict(t=30, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
                st.plotly_chart(fig, use_container_width=True, key=f"g_{chave}")

            with c2:
                st.markdown("### 📊 Estatísticas Projetadas")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.info(f"⚽ **Gols Esperados**\n\n"
                            f"• Média do Jogo: **{media_gols}**\n\n"
                            f"• Prob. Over 1.5: **{prob_over_15}**\n\n"
                            f"• Prob. Over 2.5: **{row['gols_ev']:.0f}%**")
                with col_b:
                    st.warning(f"🚩 **Escanteios**\n\n"
                               f"• Média Estimada: **{media_cantos}**\n\n"
                               f"• Prob. Over 9.5: **{row['cantos_ev']:.0f}%**")

            with c3:
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("📲 Enviar no Telegram", key=f"btn_{chave}", use_container_width=True)
                st.markdown(f"<div style='text-align:center; font-size:12px; color:#888'>{row['stats_resumo']}</div>", unsafe_allow_html=True)

            st.markdown("---")