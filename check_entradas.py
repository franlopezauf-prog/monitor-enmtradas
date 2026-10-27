"""Monitor de entradas - Semifinal URBA Top 14 (Newman vs Alumni).

Baja la pagina y, si ya NO dice "Entradas agotadas", avisa por email (Gmail)
y/o por Telegram, segun los secretos que tengas cargados.
No completa ni envia ningun formulario: la compra la confirmas vos.
"""
import os
import smtplib
import sys
import urllib.parse
import urllib.request
from email.message import EmailMessage

URL = "https://playoffsurba2026.vercel.app/"
SOLD_OUT_TEXT = "entradas agotadas"


def send_telegram(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage", data=data
    )
    urllib.request.urlopen(req, timeout=20).read()


def send_email(subject: str, text: str) -> None:
    user = os.environ["GMAIL_USER"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    to = os.environ.get("EMAIL_TO") or user
    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)


def notify(subject: str, text: str) -> None:
    """Envia por todos los canales configurados."""
    sent = False
    if os.environ.get("GMAIL_USER") and os.environ.get("GMAIL_APP_PASSWORD"):
        try:
            send_email(subject, text)
            print("Email enviado.")
            sent = True
        except Exception as exc:
            print(f"Fallo el email: {exc}")
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        try:
            send_telegram(f"{subject}\n{text}")
            print("Telegram enviado.")
            sent = True
        except Exception as exc:
            print(f"Fallo Telegram: {exc}")
    if not sent:
        raise RuntimeError("No se pudo enviar por ningun canal. Revisa los secretos.")


def fetch_page() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> int:
    if os.environ.get("TEST_NOTIFICATION") == "true":
        notify("Prueba: monitor de entradas", "Prueba OK: el monitor esta funcionando.")
        return 0

    try:
        html = fetch_page()
    except Exception as exc:  # error de red: no avisamos, reintenta en 10 min
        print(f"No se pudo leer la pagina: {exc}")
        return 1

    if SOLD_OUT_TEXT in html.lower():
        print("Sigue agotado.")
        return 0

    print("Ya NO dice 'Entradas agotadas'. Enviando aviso.")
    notify(
        "ENTRADAS DISPONIBLES - Newman vs Alumni",
        f"La pagina ya no dice 'Entradas agotadas'. Entra rapido: {URL}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
