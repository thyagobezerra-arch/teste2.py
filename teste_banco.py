import psycopg2
import pandas as pd

# COLE SEU LINK AQUI
DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:MudarAgora2026Paraiba@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

try:
    conn = psycopg2.connect(DB_URL)
    print("✅ Conectado ao banco!")
    
    # 1. Conta quantas linhas tem no total
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM analysis_logs;")
    total = cur.fetchone()[0]
    print(f"📊 Total de linhas na tabela: {total}")
    
    # 2. Mostra as 5 últimas
    print("\n🔍 Últimos 5 registros salvos:")
    df = pd.read_sql("SELECT fixture_name, created_at, mercado_tipo FROM analysis_logs ORDER BY created_at DESC LIMIT 5;", conn)
    print(df)
    
    conn.close()
except Exception as e:
    print(f"❌ Erro: {e}")