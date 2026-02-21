import psycopg2

# COLOQUE SUA URL ABAIXO
DB_URL = "postgresql://postgres.vbxmtclyraxmhvfcnfee:SF73DoFBkFGyZPiS@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

def conectar():
    try:
        conn = psycopg2.connect(DB_URL)
        print("✅ CONEXÃO ESTABELECIDA!")
        conn.close()
    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    conectar()