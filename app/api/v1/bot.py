from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.bot.telegram_bot import handle_update, verify_webhook_secret

router = APIRouter()


@router.post("/telegram/webhook", status_code=200)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> Response:
    if not await verify_webhook_secret(x_telegram_bot_api_secret_token):
        raise HTTPException(status_code=403, detail="invalid_webhook_secret")

    update = await request.json()
    await handle_update(update)
    return Response(status_code=200)
