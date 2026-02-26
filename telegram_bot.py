import requests
import os

def enviar_alerta(mensagem):
    # Tenta pegar as chaves do cofre (GitHub ou PC)
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("⚠️ Telegram não configurado (Falta Token ou ID).")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def criar_mensagem_vip(jogo, liga, ev, probabilidade, mercado):
    """Cria o texto estilo Grupo VIP"""
    return (
        f"🦁 *ALERTA EDGE PRO* 🦁\n\n"
        f"🏆 *Liga:* {liga}\n"
        f"⚽ *Jogo:* {jogo}\n"
        f"💎 *Mercado:* {mercado}\n\n"
        f"📊 *Valor Esperado (EV):* {ev:.2f}%\n"
        f"🔢 *Probabilidade Real:* {probabilidade:.1f}%\n\n"
        f"🔗 [Ver Análise Completa](https://seu-app-no-streamlit.app)"
    )