from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import ApiVersionMiddleware, add_rate_limiting

settings = get_settings()

configure_logging(settings.DEBUG)

_INSECURE_KEYS = {"change_me", "change_me_in_production_use_openssl_rand_hex_32", "", "your_secret_key"}
if settings.ENVIRONMENT.lower() in {"production", "prod"} and settings.SECRET_KEY in _INSECURE_KEYS:
    raise RuntimeError(
        "SECRET_KEY must be set to a strong random value before running. "
        "Generate one with: openssl rand -hex 32"
    )

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "X-Admin-Key"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:
        response: Response = await call_next(request)  # type: ignore[arg-type]
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ApiVersionMiddleware)
add_rate_limiting(app)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
