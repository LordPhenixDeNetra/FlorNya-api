import os
from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader

from app.config import get_settings
from app.interfaces.email_interface import IEmailService

logger = structlog.get_logger()

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"


def _get_jinja_env() -> Environment:
    return Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)


class EmailService(IEmailService):
    def __init__(self) -> None:
        self._settings = get_settings()
        self._env = _get_jinja_env()

    def _render(self, template_name: str, **ctx: object) -> str:
        tmpl = self._env.get_template(template_name)
        return tmpl.render(frontend_url=self._settings.FRONTEND_URL, **ctx)

    async def send_password_reset(self, *, to_email: str, token: str, first_name: str | None) -> None:
        reset_url = f"{self._settings.FRONTEND_URL}/reset-password?token={token}"
        html = self._render("password_reset.html", first_name=first_name, reset_url=reset_url)
        await self._send(to_email=to_email, subject="Réinitialisation de votre mot de passe FlorNya", html=html)

    async def send_welcome(self, *, to_email: str, first_name: str | None) -> None:
        html = self._render("welcome.html", first_name=first_name)
        await self._send(to_email=to_email, subject="Bienvenue sur FlorNya 🌸", html=html)

    async def send_period_reminder(
        self, *, to_email: str, first_name: str | None, days_before: int, next_period_date: str
    ) -> None:
        html = self._render(
            "period_reminder.html",
            first_name=first_name,
            days_before=days_before,
            next_period_date=next_period_date,
        )
        subject = f"Vos règles arrivent {'demain' if days_before == 1 else f'dans {days_before} jours'} 🌙"
        await self._send(to_email=to_email, subject=subject, html=html)

    async def send_subscription_confirmed(
        self, *, to_email: str, first_name: str | None, plan_name: str, plan_features: list[str]
    ) -> None:
        html = self._render(
            "subscription_confirmed.html",
            first_name=first_name,
            plan_name=plan_name,
            plan_features=plan_features,
        )
        await self._send(
            to_email=to_email,
            subject=f"Votre abonnement FlorNya {plan_name} est actif ✨",
            html=html,
        )

    async def _send(self, *, to_email: str, subject: str, html: str) -> None:
        smtp_ready = bool(self._settings.SMTP_HOST and self._settings.SMTP_PASSWORD)
        if self._settings.DEBUG or not smtp_ready:
            logger.info("email_stub", to=to_email, subject=subject)
            return

        import aiosmtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._settings.EMAIL_FROM
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))

        tls_mode = self._settings.SMTP_TLS_MODE.lower()
        use_tls = tls_mode == "ssl"       # TLS immédiat (port 465)
        start_tls = tls_mode == "starttls"  # STARTTLS (port 587)

        await aiosmtplib.send(
            msg,
            hostname=self._settings.SMTP_HOST,
            port=self._settings.SMTP_PORT,
            username=self._settings.SMTP_USER or None,
            password=self._settings.SMTP_PASSWORD,
            use_tls=use_tls,
            start_tls=start_tls,
        )
