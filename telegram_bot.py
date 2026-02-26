import requests
import os

def enviar_alerta(mensagem):
    # Tenta pegar as chaves do ambiente (GitHub ou PC)
    # Se não achar, usa os valores manuais de emergência (backup)
    token = os.getenv("TELEGRAM_TOKEN") or "8344469814:AAHvhEKG9_6qfaPc-1gdjYdcBGn6qdcfFeg"
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or "1343274781"
    
    if not token or not chat_id:
        print("⚠️ Erro: Token ou Chat ID não encontrados.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload)
        # Se quiser ver se deu certo no log:
        # print(f"Status Telegram: {response.status_code}")
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def criar_mensagem_vip(jogo, liga, ev, probabilidade, mercado):
    """
    Função obrigatória que formata o texto do alerta.
    O worker_saas.py precisa dela para funcionar.
    """
    return (
        f"🦁 *ALERTA EDGE PRO* 🦁\n\n"
        f"🏆 *Liga:* {liga}\n"
        f"⚽ *Jogo:* {jogo}\n"
        f"💎 *Mercado:* {mercado}\n\n"
        f"📊 *Valor Esperado (EV):* {ev:.2f}%\n"
        f"🔢 *Probabilidade Real:* {probabilidade:.1f}%\n\n"
        f"🚀 *Ação:* Entrar AGORA!"
    )