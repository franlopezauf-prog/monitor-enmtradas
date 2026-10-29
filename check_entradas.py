"""Monitor de entradas - Semifinal URBA Top 14 (Newman vs Alumni).
 
La pagina carga su contenido con JavaScript (al principio dice "Cargando..."),
asi que abrimos un navegador real (Playwright), esperamos a que termine de
cargar y leemos el texto que ve una persona. Si NO dice "agotadas", avisamos
por email (Gmail) y/o Telegram. No completa ningun formulario.
"""
import os
import smtplib
import sys
import urllib.parse
import urllib.request
from email.message import EmailMessage
 
URL = "https://playoffsurba2026.vercel.app/"
SOLD_OUT_WORD = "agotad"  # agotada / agotadas / agotado
 
 
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
 
 
def get_page_text() -> str:
    """Abre la pagina en un navegador y devuelve el texto ya cargado."""
    from playwright.sync_api import sync_playwright
 
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle", timeout=45000)
        try:
            # esperar a que desaparezca el "Cargando..."
            page.wait_for_function(
                "() => !document.body.innerText.toLowerCase().includes('cargando')",
                timeout=20000,
            )
        except Exception:
            pass
        text = page.inner_text("body")
        browser.close()
        return text
 
 
def main() -> int:
    if os.environ.get("TEST_NOTIFICATION") == "true":
        notify("Prueba: monitor de entradas", "Prueba OK: el monitor esta funcionando.")
        return 0
 
    try:
        text = get_page_text()
    except Exception as exc:  # error de red o navegador: no avisamos
        print(f"No se pudo leer la pagina: {exc}")
        return 1
 
    lower = text.lower()
    resumen = " | ".join(line.strip() for line in text.splitlines() if line.strip())
    print(f"Texto visto en la pagina: {resumen[:400]}")
 
    if "cargando" in lower:
        print("La pagina no termino de cargar. No se avisa; se reintenta luego.")
        return 1
 
    if SOLD_OUT_WORD in lower:
        print("Sigue agotado.")
        return 0
 
    print("La pagina cargo y NO dice 'agotadas'. Enviando aviso.")
    notify(
        "ENTRADAS DISPONIBLES - Newman vs Alumni",
        f"La pagina ya no dice 'Entradas agotadas'. Entra rapido: {URL}",
    )
    return 0
 
 
if __name__ == "__main__":
    sys.exit(main())
 
