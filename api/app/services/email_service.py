from email.message import EmailMessage
from typing import Optional
import aiosmtplib
from app.config import settings


async def send_email(to_email: str, subject: str, html: str, text: Optional[str] = None) -> bool:
    """Envoie un email HTML (avec texte optionnel) via SMTP configuré.

    Retourne True si l'envoi a réussi, False sinon.
    """
    # Vérifier configuration minimale
    if not settings.smtp_host or not settings.smtp_port or not settings.sender_email:
        print("[email] SMTP non configuré correctement; email non envoyé.")
        return False

    msg = EmailMessage()
    sender = f"{settings.sender_name} <{settings.sender_email}>" if settings.sender_name else settings.sender_email
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    if text:
        msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    use_starttls = True
    try:
        if use_starttls:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                start_tls=True,
                username=settings.smtp_user,
                password=settings.smtp_password,
            )
        else:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
            )
        print(f"[email] Sent to {to_email} — subject='{subject}'")
        return True
    except Exception as e:
        print(f"[email] Échec envoi à {to_email}: {e}")
        return False
