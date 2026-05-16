"""Telegram Bot webhook handler for FlorNya notifications and quick queries."""
import hashlib
import hmac
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TELEGRAM_API = "https://api.telegram.org"


async def verify_webhook_secret(secret_token: str | None) -> bool:
    """Validate the X-Telegram-Bot-Api-Secret-Token header."""
    if not settings.TELEGRAM_WEBHOOK_SECRET:
        return True
    if secret_token is None:
        return False
    return hmac.compare_digest(secret_token, settings.TELEGRAM_WEBHOOK_SECRET)


async def send_message(chat_id: int | str, text: str, parse_mode: str = "HTML") -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.info("[TELEGRAM-STUB] chat_id=%s text=%r", chat_id, text[:80])
        return True
    url = f"{TELEGRAM_API}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode})
        if resp.status_code != 200:
            logger.error("Telegram sendMessage failed: %s", resp.text)
            return False
    return True


async def handle_update(update: dict) -> None:
    """Route an incoming Telegram update to the appropriate handler."""
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    text: str = message.get("text", "").strip()

    if text.startswith("/start"):
        await send_message(
            chat_id,
            "👋 <b>Bienvenue sur FlorNya Bot !</b>\n\n"
            "Je suis votre assistant santé féminine. Commandes disponibles :\n"
            "• /status — Votre statut de cycle actuel\n"
            "• /help — Aide et informations",
        )
    elif text.startswith("/help"):
        await send_message(
            chat_id,
            "<b>Aide FlorNya Bot</b>\n\n"
            "Connectez votre compte FlorNya pour recevoir :\n"
            "• Rappels de période\n"
            "• Check-ins émotionnels\n"
            "• Notifications de rendez-vous\n\n"
            "Configurez vos notifications sur app.flornya.app",
        )
    elif text.startswith("/status"):
        await send_message(
            chat_id,
            "ℹ️ Connectez votre compte FlorNya sur app.flornya.app "
            "pour accéder à votre statut de cycle en temps réel.",
        )
    else:
        await send_message(
            chat_id,
            "Je n'ai pas compris cette commande. Tapez /help pour la liste des commandes.",
        )
