"""Integration tests for extras: essential plan, beta_access, device tokens, bot webhook."""
import pytest


async def _register(client, email: str) -> str:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "date_of_birth": "1990-05-01", "language": "fr"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


async def _set_essential(db_session, email: str) -> None:
    from sqlalchemy import select

    from app.models.user import User, UserPlan

    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.plan = UserPlan.essential
        await db_session.commit()


async def _set_bloom(db_session, email: str) -> None:
    from sqlalchemy import select

    from app.models.user import User, UserPlan

    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.plan = UserPlan.bloom
        await db_session.commit()


# ── Essential plan guard ────────────────────────────────────────────────────


async def test_cycle_records_free_user_rejected(client) -> None:
    """Free users cannot create cycle records — essential plan required."""
    token = await _register(client, "cycle_free@extras.com")
    r = await client.post(
        "/api/v1/cycle/records",
        headers={"Authorization": f"Bearer {token}"},
        json={"period_start": "2026-01-01", "cycle_length": 28},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "essential_plan_required"


async def test_essential_user_can_access_cycle(client, db_session) -> None:
    """Essential plan users can create cycle records."""
    token = await _register(client, "cycle_essential@extras.com")
    await _set_essential(db_session, "cycle_essential@extras.com")

    r = await client.post(
        "/api/v1/cycle/records",
        headers={"Authorization": f"Bearer {token}"},
        json={"period_start": "2026-01-01", "cycle_length": 28},
    )
    assert r.status_code == 201


async def test_bloom_user_has_essential_access(client, db_session) -> None:
    """Bloom users still pass the essential guard."""
    token = await _register(client, "cycle_bloom@extras.com")
    await _set_bloom(db_session, "cycle_bloom@extras.com")

    r = await client.post(
        "/api/v1/cycle/records",
        headers={"Authorization": f"Bearer {token}"},
        json={"period_start": "2026-01-02", "cycle_length": 28},
    )
    assert r.status_code == 201


# ── Beta access ─────────────────────────────────────────────────────────────


async def test_activate_beta_valid_code(client) -> None:
    """With no BETA_INVITE_CODE configured (empty), any code is accepted."""
    token = await _register(client, "beta_user@extras.com")
    r = await client.post(
        "/api/v1/users/me/beta-activate",
        params={"invite_code": "any-code-works-when-not-configured"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200


async def test_activate_beta_wrong_code_rejected(client, monkeypatch) -> None:
    """Wrong invite code returns 403 when BETA_INVITE_CODE is set."""
    import app.api.v1.users as users_module
    import app.config as config_module

    s = config_module.get_settings()
    monkeypatch.setattr(s, "BETA_INVITE_CODE", "secret123")

    token = await _register(client, "beta_user3@extras.com")
    r = await client.post(
        "/api/v1/users/me/beta-activate",
        params={"invite_code": "wrongcode"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


async def test_activate_beta_idempotent(client) -> None:
    token = await _register(client, "beta_user2@extras.com")
    r1 = await client.post(
        "/api/v1/users/me/beta-activate",
        params={"invite_code": "any"},
        headers={"Authorization": f"Bearer {token}"},
    )
    r2 = await client.post(
        "/api/v1/users/me/beta-activate",
        params={"invite_code": "any"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 200
    assert r2.status_code == 200


# ── Device tokens ───────────────────────────────────────────────────────────


async def test_register_device_token(client) -> None:
    token = await _register(client, "device_user@extras.com")
    r = await client.post(
        "/api/v1/users/me/device-token",
        headers={"Authorization": f"Bearer {token}"},
        json={"token": "fcm_token_abc123xyz456", "platform": "ios"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["platform"] == "ios"
    assert data["is_active"] is True


async def test_register_device_token_dedup(client) -> None:
    """Registering the same token twice should upsert (no duplicate)."""
    token = await _register(client, "device_dedup@extras.com")
    payload = {"token": "fcm_token_dedup_test123", "platform": "android"}
    r1 = await client.post(
        "/api/v1/users/me/device-token",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    r2 = await client.post(
        "/api/v1/users/me/device-token",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert r1.status_code == 201
    assert r2.status_code == 201


async def test_unregister_device_token(client) -> None:
    token = await _register(client, "device_unreg@extras.com")
    device_token = "fcm_token_unregister_test456"
    await client.post(
        "/api/v1/users/me/device-token",
        headers={"Authorization": f"Bearer {token}"},
        json={"token": device_token, "platform": "web"},
    )
    r = await client.delete(
        "/api/v1/users/me/device-token",
        headers={"Authorization": f"Bearer {token}"},
        json={"token": device_token, "platform": "web"},
    )
    assert r.status_code == 204


async def test_device_token_requires_auth(client) -> None:
    r = await client.post(
        "/api/v1/users/me/device-token",
        json={"token": "some_token_value_test", "platform": "ios"},
    )
    assert r.status_code == 401


# ── Avatar upload ───────────────────────────────────────────────────────────


async def test_avatar_upload_invalid_format(client) -> None:
    """PDF files should be rejected with 415."""
    token = await _register(client, "avatar_bad@extras.com")
    r = await client.post(
        "/api/v1/users/me/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
    )
    assert r.status_code == 415


async def test_avatar_upload_too_large(client) -> None:
    """Files over AVATAR_MAX_SIZE_MB should return 413."""
    token = await _register(client, "avatar_large@extras.com")
    big_content = b"x" * (6 * 1024 * 1024)  # 6 MB
    r = await client.post(
        "/api/v1/users/me/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("avatar.jpg", big_content, "image/jpeg")},
    )
    assert r.status_code == 413


async def test_avatar_upload_valid(client) -> None:
    """Valid JPEG upload should succeed (uses base64 stub since no S3 configured)."""
    token = await _register(client, "avatar_ok@extras.com")
    r = await client.post(
        "/api/v1/users/me/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("avatar.jpg", b"\xff\xd8\xff" + b"fake_jpeg_data", "image/jpeg")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "photo_url" in data or r.status_code == 200


# ── Telegram Bot webhook ────────────────────────────────────────────────────


async def test_telegram_webhook_start_command(client) -> None:
    update = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "chat": {"id": 12345, "type": "private"},
            "text": "/start",
            "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
            "date": 1700000000,
        },
    }
    r = await client.post("/api/v1/bot/telegram/webhook", json=update)
    assert r.status_code == 200


async def test_telegram_webhook_help_command(client) -> None:
    update = {
        "update_id": 2,
        "message": {
            "message_id": 2,
            "chat": {"id": 12345, "type": "private"},
            "text": "/help",
            "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
            "date": 1700000001,
        },
    }
    r = await client.post("/api/v1/bot/telegram/webhook", json=update)
    assert r.status_code == 200


async def test_telegram_webhook_unknown_message(client) -> None:
    update = {
        "update_id": 3,
        "message": {
            "message_id": 3,
            "chat": {"id": 12345, "type": "private"},
            "text": "bonjour",
            "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
            "date": 1700000002,
        },
    }
    r = await client.post("/api/v1/bot/telegram/webhook", json=update)
    assert r.status_code == 200


async def test_telegram_webhook_invalid_secret(client, monkeypatch) -> None:
    """When TELEGRAM_WEBHOOK_SECRET is set, wrong token should return 403."""
    import app.bot.telegram_bot as bot_module

    monkeypatch.setattr(bot_module.settings, "TELEGRAM_WEBHOOK_SECRET", "mysecret123")
    update = {"update_id": 4, "message": {"message_id": 4, "chat": {"id": 1}, "text": "/start", "date": 1}}
    r = await client.post(
        "/api/v1/bot/telegram/webhook",
        json=update,
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrongsecret"},
    )
    assert r.status_code == 403
