import base64
import secrets
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: UUID, token_version: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "typ": "access",
        "exp": expire,
        "ver": token_version,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: UUID, token_version: int) -> tuple[str, str]:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = secrets.token_urlsafe(32)
    payload = {
        "sub": str(user_id),
        "typ": "refresh",
        "exp": expire,
        "jti": jti,
        "ver": token_version,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM), jti


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError("invalid_token") from exc


def verify_minimum_age(date_of_birth: date) -> None:
    age = (date.today() - date_of_birth).days // 365
    if age < settings.MINIMUM_AGE:
        raise ValueError("minimum_age_not_met")


def is_adult(date_of_birth: date) -> bool:
    age = (date.today() - date_of_birth).days // 365
    return age >= settings.ADULT_CONTENT_AGE


def _normalize_fernet_key(key: str) -> bytes:
    raw = key.encode()
    try:
        decoded = base64.urlsafe_b64decode(raw)
    except Exception as exc:
        raise ValueError("invalid_encryption_key") from exc
    if len(decoded) != 32:
        raise ValueError("invalid_encryption_key")
    return raw


def get_fernet() -> Fernet:
    key = _normalize_fernet_key(settings.ENCRYPTION_KEY)
    return Fernet(key)


def encrypt_sensitive(value: str | None) -> str | None:
    if value is None:
        return None
    token = get_fernet().encrypt(value.encode())
    return token.decode()


def decrypt_sensitive(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        plaintext = get_fernet().decrypt(value.encode())
    except InvalidToken as exc:
        raise ValueError("invalid_ciphertext") from exc
    return plaintext.decode()
