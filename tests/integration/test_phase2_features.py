"""Integration tests for Phase 2 features (Fertility, Pregnancy, Hormonal Health, Menopause, Nutrition)."""
from datetime import date, timedelta


async def _register_bloom(client, email: str) -> str:
    """Register a user and manually give them bloom plan (test helper)."""
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "date_of_birth": "1990-05-01", "language": "fr"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]

    from app.models.user import UserPlan
    return token


async def _register(client, email: str) -> str:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "date_of_birth": "1990-05-01", "language": "fr"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


async def _set_bloom(db_session, email: str) -> None:
    from sqlalchemy import select, update
    from app.models.user import User, UserPlan
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.plan = UserPlan.bloom
        await db_session.commit()


async def _set_bloom_pro(db_session, email: str) -> None:
    from sqlalchemy import select
    from app.models.user import User, UserPlan
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.plan = UserPlan.bloom_pro
        await db_session.commit()


# ── Fertility ──────────────────────────────────────────────────────────────


async def test_fertility_requires_bloom(client) -> None:
    token = await _register(client, "fert_free@example.com")
    r = await client.post(
        "/api/v1/fertility/logs",
        headers={"Authorization": f"Bearer {token}"},
        json={"log_date": str(date.today()), "bbt_celsius": "36.5"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "bloom_plan_required"


async def test_log_and_list_fertility(client, db_session) -> None:
    email = "fert_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    today = str(date.today())
    r = await client.post(
        "/api/v1/fertility/logs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "log_date": today,
            "bbt_celsius": "36.7",
            "cervical_mucus": "egg_white",
            "lh_test_result": "positive",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["bbt_celsius"] == "36.7"
    assert data["cervical_mucus"] == "egg_white"
    assert data["lh_test_result"] == "positive"

    r2 = await client.get("/api/v1/fertility/logs", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert len(r2.json()) == 1


async def test_log_conception_attempt(client, db_session) -> None:
    email = "attempt_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/fertility/attempts",
        headers={"Authorization": f"Bearer {token}"},
        json={"attempt_date": str(date.today()), "notes": "test privé"},
    )
    assert r.status_code == 200
    assert r.json()["notes"] == "test privé"

    r2 = await client.get("/api/v1/fertility/attempts", headers={"Authorization": f"Bearer {token}"})
    assert len(r2.json()) == 1


# ── Pregnancy ──────────────────────────────────────────────────────────────


async def test_pregnancy_requires_bloom(client) -> None:
    token = await _register(client, "preg_free@example.com")
    r = await client.post(
        "/api/v1/pregnancy/activate",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert r.status_code == 403


async def test_activate_pregnancy(client, db_session) -> None:
    email = "preg_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    lmp = str(date.today() - timedelta(days=56))
    r = await client.post(
        "/api/v1/pregnancy/activate",
        headers={"Authorization": f"Bearer {token}"},
        json={"lmp_date": lmp},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "active"
    assert data["current_week"] == 8


async def test_get_week_info(client, db_session) -> None:
    email = "week_info@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.get("/api/v1/pregnancy/week/20", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["week"] == 20
    assert data["trimester"] == 2
    assert "baby_size_comparison" in data


async def test_log_pregnancy_symptoms(client, db_session) -> None:
    email = "preg_sym@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/pregnancy/symptoms",
        headers={"Authorization": f"Bearer {token}"},
        json={"log_date": str(date.today()), "nausea": True, "fatigue": True, "severity": 3},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["nausea"] is True
    assert data["is_alarm_symptom"] is False


async def test_create_appointment(client, db_session) -> None:
    email = "appt@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/pregnancy/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "appointment_date": str(date.today() + timedelta(days=14)),
            "title": "Échographie T2",
            "appointment_type": "ultrasound",
        },
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Échographie T2"


async def test_epds_low_score(client, db_session) -> None:
    email = "epds_ok@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/pregnancy/epds",
        headers={"Authorization": f"Bearer {token}"},
        json={"answers": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total_score"] == 1
    assert data["alert_level"] == "normal"


async def test_epds_high_score_alert(client, db_session) -> None:
    email = "epds_alert@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/pregnancy/epds",
        headers={"Authorization": f"Bearer {token}"},
        json={"answers": [3, 3, 3, 2, 2, 2, 1, 1, 1, 1]},
    )
    assert r.status_code == 200
    assert r.json()["alert_level"] == "alert"
    assert r.json()["total_score"] == 19


# ── Hormonal Health ────────────────────────────────────────────────────────


async def test_log_pain(client, db_session) -> None:
    email = "pain_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/hormonal-health/pain",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "log_date": str(date.today()),
            "pain_intensity": 7,
            "pelvic": True,
            "dysmenorrhea": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["pain_intensity"] == 7
    assert data["pelvic"] is True


async def test_pcos_assessment_low_risk(client, db_session) -> None:
    email = "pcos_low@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/hormonal-health/pcos/assessment",
        headers={"Authorization": f"Bearer {token}"},
        json={"irregular_cycles": False, "acne": False, "weight_gain": False},
    )
    assert r.status_code == 200
    assert r.json()["risk_level"] == "low"


async def test_pcos_assessment_high_risk(client, db_session) -> None:
    email = "pcos_high@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/hormonal-health/pcos/assessment",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "irregular_cycles": True, "excess_hair_growth": True, "acne": True,
            "weight_gain": True, "hair_loss": True, "difficulty_conceiving": True,
        },
    )
    assert r.status_code == 200
    assert r.json()["risk_level"] == "high"


async def test_endo_resources(client, db_session) -> None:
    email = "endo_resources@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.get(
        "/api/v1/hormonal-health/endometriosis/resources",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "common_symptoms" in data
    assert len(data["common_symptoms"]) > 0


async def test_add_hormonal_treatment(client) -> None:
    from tests.integration.test_phase1_features import _register_and_login
    token = await _register_and_login(client, "treatment@example.com")

    r = await client.post(
        "/api/v1/hormonal-health/treatments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "treatment_type": "pill",
            "brand_name": "Jasmine",
            "start_date": str(date.today()),
            "reminder_time": "08:00",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["treatment_type"] == "pill"
    assert data["brand_name"] == "Jasmine"
    assert data["is_active"] is True


# ── Menopause ──────────────────────────────────────────────────────────────


async def test_log_menopause_symptoms(client, db_session) -> None:
    email = "meno_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/menopause/logs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "log_date": str(date.today()),
            "hot_flash_count": 4,
            "night_sweats": True,
            "insomnia": True,
            "severity": 3,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["hot_flash_count"] == 4
    assert data["night_sweats"] is True


async def test_quick_hot_flash(client, db_session) -> None:
    email = "hotflash@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    today = str(date.today())
    r = await client.post(
        "/api/v1/menopause/hot-flash",
        headers={"Authorization": f"Bearer {token}"},
        json={"log_date": today, "count": 2},
    )
    assert r.status_code == 200
    assert r.json()["hot_flash_count"] == 2

    r2 = await client.post(
        "/api/v1/menopause/hot-flash",
        headers={"Authorization": f"Bearer {token}"},
        json={"log_date": today, "count": 3},
    )
    assert r2.status_code == 200
    assert r2.json()["hot_flash_count"] == 5


async def test_perimenopause_screening(client, db_session) -> None:
    email = "peri_screen@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/menopause/perimenopause/screening",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "age": 47,
            "irregular_cycles": True,
            "hot_flashes": True,
            "night_sweats": True,
            "vaginal_dryness": True,
            "sleep_issues": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] in ("élevé", "modéré", "faible")
    assert len(data["detected_signs"]) > 0


# ── Nutrition ──────────────────────────────────────────────────────────────


async def test_log_meals(client, db_session) -> None:
    email = "nutrition_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/nutrition/logs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "log_date": str(date.today()),
            "meals": ["Porridge avoine", "Salade lentilles saumon", "Soupe courge"],
            "water_glasses": 8,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["meals"] == ["Porridge avoine", "Salade lentilles saumon", "Soupe courge"]
    assert data["water_glasses"] == 8


async def test_get_nutritional_plan(client, db_session) -> None:
    email = "nutri_plan@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.get(
        "/api/v1/nutrition/plan?phase=menstrual",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["phase"] == "menstrual"
    assert len(data["key_nutrients"]) > 0
    assert len(data["recommended_foods"]) > 0


async def test_get_recipes(client, db_session) -> None:
    email = "recipes_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.get(
        "/api/v1/nutrition/recipes?phase=luteal",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    recipes = r.json()
    assert len(recipes) >= 1
    assert all(recipe["phase"] == "luteal" for recipe in recipes)


async def test_get_supplements(client, db_session) -> None:
    email = "suppl_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.get(
        "/api/v1/nutrition/supplements?phase=luteal",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    sups = r.json()
    assert len(sups) > 0
    assert all("luteal" in s["phases_recommended"] for s in sups)
