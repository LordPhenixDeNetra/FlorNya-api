from collections.abc import Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings
from app.core.security import decode_token

settings = get_settings()


def _rate_limit_key(request: Request) -> str:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
            sub = payload.get("sub")
            if isinstance(sub, str) and sub:
                return sub
        except Exception:
            pass
    return get_remote_address(request) or "anonymous"


limiter = Limiter(key_func=_rate_limit_key, default_limits=[settings.RATE_LIMIT_DEFAULT])


class ApiVersionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["API-Version"] = settings.APP_VERSION
        return response


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "rate_limit_exceeded"})


def add_rate_limiting(app) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
