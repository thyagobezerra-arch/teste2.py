import requests

# COLE SEUS DADOS AQUI
TOKEN = "SEU_TOKEN_DO_BOTFATHER"
CHAT_ID = "SEU_CHAT_ID_DO_USERINFOBOT"

def enviar_teste():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "🦁 *EDGE PRO ATIVO!*\n\nConexão estabelecida com sucesso. O Sniper está pronto para caçar Green! 🎯",
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload)
    print(r.json())

enviar_teste()