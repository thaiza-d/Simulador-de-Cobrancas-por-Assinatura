import requests
from ..config import RESEND_API_KEY

def enviar_email_alerta(email_destino: str):
    url = "https://api.resend.com/emails"
    headers = {"Authorization": f"Bearer {RESEND_API_KEY}"}
    data ={
        "from": "seguranca@assinaturas.com",
        "to": email_destino,
        "subject": "Alerta de tentativas de acesso ao login",
        "text": "Olá! Detectamos várias tentativas de login na sua conta. Se for você que está realizando essas tentativas, desconsidere a mensagem. Caso não for você, recomendamos que altere a sua senha imediatamente!"
    }
    requests.post(url, headers=headers, json=data)