"""Push notification service — Firebase FCM with graceful stub fallback."""
import hashlib
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PushNotificationService:
    """Sends FCM push notifications. Falls back to logging when Firebase is not configured."""

    def __init__(self) -> None:
        self._fcm_app = None
        if settings.FIREBASE_CREDENTIALS_PATH and settings.FIREBASE_PROJECT_ID:
            try:
                import firebase_admin
                from firebase_admin import credentials

                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                if not firebase_admin._apps:
                    self._fcm_app = firebase_admin.initialize_app(cred)
                else:
                    self._fcm_app = firebase_admin.get_app()
            except Exception as exc:
                logger.warning("Firebase init failed — falling back to stub: %s", exc)

    @staticmethod
    def _token_hint(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()[:16]

    async def send(self, token: str, title: str, body: str, data: dict | None = None) -> bool:
        """Send a push notification. Returns True on success."""
        if self._fcm_app is None:
            logger.info("[PUSH-STUB] token_hint=%s title=%r body=%r", self._token_hint(token), title, body)
            return True

        try:
            from firebase_admin import messaging

            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                token=token,
            )
            messaging.send(message, app=self._fcm_app)
            return True
        except Exception as exc:
            logger.error("FCM send error: %s", exc)
            return False

    async def send_multicast(self, tokens: list[str], title: str, body: str, data: dict | None = None) -> int:
        """Send to multiple tokens. Returns count of successful sends."""
        if not tokens:
            return 0

        if self._fcm_app is None:
            for token in tokens:
                logger.info("[PUSH-STUB] token_hint=%s title=%r", self._token_hint(token), title)
            return len(tokens)

        try:
            from firebase_admin import messaging

            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                tokens=tokens,
            )
            response = messaging.send_each_for_multicast(message, app=self._fcm_app)
            return response.success_count
        except Exception as exc:
            logger.error("FCM multicast error: %s", exc)
            return 0
