"""Integration tests for Phase 1 features."""
from datetime import date, timedelta


async def _register_and_login(client, email="user_p1@example.com") -> str:
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "date_of_birth": "1995-06-15",
            "language": "fr",
        },
    )
    assert r.status_code == 200
    return r.json()["access_token"]


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_register_returns_user_fields(client) -> None:
    token = await _register_and_login(client, "fields_test@example.com")
    r = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    data = r.json()
    assert r.status_code == 200
    assert "onboarding_completed" in data
    assert data["onboarding_completed"] is False
    assert "is_2fa_enabled" in data
    assert data["is_2fa_enabled"] is False


async def test_update_me_first_name(client) -> None:
    token = await _register_and_login(client, "fname_test@example.com")
    r = await client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"first_name": "Fatou"},
    )
    assert r.status_code == 200
    assert r.json()["first_name"] == "Fatou"


async def test_onboarding_complete(client) -> None:
    token = await _register_and_login(client, "onboard@example.com")
    r = await client.post(
        "/api/v1/users/me/onboarding",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "first_name": "Awa",
            "reproductive_stage": "regular",
            "cycle_length": 28,
            "period_length": 5,
            "timezone": "Europe/Paris",
            "health_conditions": [],
            "cuisine_preference": "west_african",
        },
    )
    assert r.status_code == 200
    assert r.json()["onboarding_completed"] is True
    assert r.json()["first_name"] == "Awa"


async def test_export_data_json(client) -> None:
    token = await _register_and_login(client, "export_test@example.com")
    r = await client.get(
        "/api/v1/users/me/export?format=json",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")


async def test_export_data_csv(client) -> None:
    token = await _register_and_login(client, "export_csv@example.com")
    r = await client.get(
        "/api/v1/users/me/export?format=csv",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


async def test_delete_account(client) -> None:
    token = await _register_and_login(client, "delete_me@example.com")
    r = await client.delete("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 204

    r2 = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 401


# ── Cycle ─────────────────────────────────────────────────────────────────────


async def test_create_cycle_record_with_flow(client) -> None:
    token = await _register_and_login(client, "cycle_flow@example.com")
    period_start = str(date.today() - timedelta(days=5))
    r = await client.post(
        "/api/v1/cycle/records",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "period_start": period_start,
            "period_end": str(date.today() - timedelta(days=1)),
            "cycle_length": 28,
            "flow_intensity": "medium",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["flow_intensity"] == "medium"
    assert data["period_end"] is not None


async def test_get_calendar(client) -> None:
    token = await _register_and_login(client, "calendar_test@example.com")
    period_start = str(date.today().replace(day=1))
    await client.post(
        "/api/v1/cycle/records",
        headers={"Authorization": f"Bearer {token}"},
        json={"period_start": period_start, "cycle_length": 28},
    )
    today = date.today()
    r = await client.get(
        f"/api/v1/cycle/calendar?year={today.year}&month={today.month}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["year"] == today.year
    assert data["month"] == today.month
    assert len(data["days"]) > 0
    day_keys = {"date", "phase", "cycle_day", "is_period", "is_fertile", "has_symptoms", "has_mood"}
    assert day_keys.issubset(set(data["days"][0].keys()))


async def test_log_and_list_symptoms(client) -> None:
    token = await _register_and_login(client, "symptoms_test@example.com")
    today = str(date.today())
    r = await client.post(
        "/api/v1/cycle/symptoms",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "log_date": today,
            "cramps": True,
            "bloating": False,
            "headache": True,
            "fatigue": True,
            "energy": 2,
            "sleep_quality": 3,
            "intensity": 2,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["cramps"] is True
    assert data["headache"] is True
    assert data["energy"] == 2

    r2 = await client.get(
        "/api/v1/cycle/symptoms",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    assert len(r2.json()) == 1


async def test_symptom_upsert(client) -> None:
    token = await _register_and_login(client, "upsert_sym@example.com")
    today = str(date.today())
    await client.post(
        "/api/v1/cycle/symptoms",
        headers={"Authorization": f"Bearer {token}"},
        json={"log_date": today, "cramps": True, "energy": 1},
    )
    r = await client.post(
        "/api/v1/cycle/symptoms",
        headers={"Authorization": f"Bearer {token}"},
        json={"log_date": today, "cramps": False, "energy": 5},
    )
    assert r.status_code == 200

    r2 = await client.get(
        "/api/v1/cycle/symptoms",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert len(r2.json()) == 1


# ── Reminders ─────────────────────────────────────────────────────────────────


async def test_create_and_list_reminders(client) -> None:
    token = await _register_and_login(client, "reminders_test@example.com")
    r = await client.put(
        "/api/v1/reminders/period",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_enabled": True, "time_of_day": "08:00", "label": "Rappel période"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["reminder_type"] == "period"
    assert data["time_of_day"] == "08:00"
    assert data["label"] == "Rappel période"

    r2 = await client.get("/api/v1/reminders", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert len(r2.json()) == 1


async def test_delete_reminder(client) -> None:
    token = await _register_and_login(client, "del_reminder@example.com")
    await client.put(
        "/api/v1/reminders/hydration",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_enabled": True, "time_of_day": "10:00"},
    )
    r = await client.delete(
        "/api/v1/reminders/hydration",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 204

    r2 = await client.get("/api/v1/reminders", headers={"Authorization": f"Bearer {token}"})
    assert r2.json() == []


async def test_delete_nonexistent_reminder_returns_404(client) -> None:
    token = await _register_and_login(client, "noreminder@example.com")
    r = await client.delete(
        "/api/v1/reminders/medication",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


# ── 2FA ──────────────────────────────────────────────────────────────────────


async def test_2fa_setup_requires_auth(client) -> None:
    r = await client.post("/api/v1/auth/2fa/setup")
    assert r.status_code == 401


async def test_2fa_setup_and_confirm(client) -> None:
    token = await _register_and_login(client, "2fa_test@example.com")
    r = await client.post("/api/v1/auth/2fa/setup", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "secret" in data
    assert "qr_code_base64" in data
    assert "otpauth_url" in data

    import pyotp
    totp = pyotp.TOTP(data["secret"])
    code = totp.now()

    r2 = await client.post(
        "/api/v1/auth/2fa/confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": code},
    )
    assert r2.status_code == 204


# ── Password reset ────────────────────────────────────────────────────────────


async def test_password_reset_request_unknown_email(client) -> None:
    r = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "nobody@example.com"},
    )
    assert r.status_code == 204


async def test_password_reset_invalid_token(client) -> None:
    r = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "badtoken", "new_password": "newpass123"},
    )
    assert r.status_code == 400
