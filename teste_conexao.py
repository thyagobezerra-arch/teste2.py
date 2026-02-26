import requests

# 1. SUBSTITUA PELOS SEUS DADOS REAIS
TOKEN = "COLE_AQUI_O_TOKEN_DO_BOTFATHER"
CHAT_ID = "COLE_AQUI_O_ID_DO_USERINFOBOT"

def testar_notificacao():
    """Envia uma mensagem de teste formatada para o seu Telegram"""
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # Mensagem estilizada para confirmar que o bot está pronto para o seu SaaS
    texto = (
        "🚀 *EDGE PRO: CONEXÃO ATIVA*\n\n"
        "O bot foi configurado corretamente e já consegue se comunicar com o sistema.\n\n"
        "✅ *Status:* Online\n"
        "📍 *Local:* João Pessoa/PB\n"
        "🎯 *Próximo passo:* Integrar os alertas de valor."
    )
    
    payload = {
        "chat_id": CHAT_ID,
        "text": texto,
        "parse_mode": "Markdown"
    }

    print("--- Iniciando teste de envio ---")
    try:
        response = requests.post(url, json=payload)
        resultado = response.json()
        
        if resultado.get("ok"):
            print("✅ SUCESSO! Verifique seu Telegram.")
        else:
            print(f"❌ ERRO DO TELEGRAM: {resultado.get('description')}")
            
    except Exception as e:
        print(f"❌ ERRO DE CONEXÃO: {e}")

if __name__ == "__main__":
    testar_notificacao()