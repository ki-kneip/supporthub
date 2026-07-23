import os
import requests

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

def send_email(to_email, to_name, subject, html_content):
    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("BREVO_SENDER_EMAIL")

    if not api_key or not sender_email:
        print(f"[EMAIL:CONSOLE] Para: {to_name} <{to_email}> | Assunto: {subject}\n{html_content}")
        return

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
    }

    data = {
        "sender": {
            "email": sender_email,
            "name": "supporthub noreply",
        },
        "subject": subject,
        "htmlContent": html_content,
        "to": [{
            "email": to_email,
            "name": to_name,
        }],
    }

    response = requests.post(BREVO_API_URL, headers=headers, json=data)
    response.raise_for_status()
    return response