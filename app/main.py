from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import ApiVersionMiddleware, add_rate_limiting

settings = get_settings()

configure_logging(settings.DEBUG)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ApiVersionMiddleware)
add_rate_limiting(app)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
