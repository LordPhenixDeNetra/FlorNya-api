"""Integration tests for Phase 3 features (Mental, Intimate, Community, Consultation, Chat, Dashboard)."""
from datetime import date, timedelta


async def _register(client, email: str) -> str:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "date_of_birth": "1990-05-01", "language": "fr"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


async def _register_teen(client, email: str) -> str:
    """Register a minor (15 years old)."""
    dob = str(date.today().replace(year=date.today().year - 15))
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "date_of_birth": dob, "language": "fr"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


async def _set_bloom(db_session, email: str) -> None:
    from sqlalchemy import select
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


# ── Dashboard ──────────────────────────────────────────────────────────────


async def test_dashboard_empty(client) -> None:
    token = await _register(client, "dash_empty@example.com")
    r = await client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "plan" in data
    assert data["plan"] == "free"
    assert "mood" in data
    assert data["cycle"] is None


async def test_dashboard_with_cycle(client, db_session) -> None:
    token = await _register(client, "dash_cycle@example.com")
    await _set_bloom(db_session, "dash_cycle@example.com")  # bloom includes essential
    today = str(date.today() - timedelta(days=7))
    await client.post(
        "/api/v1/cycle/records",
        headers={"Authorization": f"Bearer {token}"},
        json={"period_start": today, "cycle_length": 28},
    )
    r = await client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["cycle"] is not None
    assert data["cycle"]["current_phase"] is not None
    assert data["cycle"]["cycle_day"] is not None


# ── Mental Health ──────────────────────────────────────────────────────────


async def test_create_mood_triggers_no_alert(client, db_session) -> None:
    token = await _register(client, "mood_good@example.com")
    await _set_bloom(db_session, "mood_good@example.com")  # bloom includes essential
    r = await client.post(
        "/api/v1/mental/mood",
        headers={"Authorization": f"Bearer {token}"},
        json={"log_date": str(date.today()), "mood_score": 4},
    )
    assert r.status_code == 200
    assert r.json()["mood_score"] == 4


async def test_journal_requires_bloom(client) -> None:
    token = await _register(client, "journal_free@example.com")
    r = await client.post(
        "/api/v1/mental/journal",
        headers={"Authorization": f"Bearer {token}"},
        json={"log_date": str(date.today()), "text": "Mon journal", "prompt_type": "free"},
    )
    assert r.status_code == 403


async def test_add_and_list_journal(client, db_session) -> None:
    email = "journal_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/mental/journal",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "log_date": str(date.today()),
            "text": "Aujourd'hui je me sens bien malgré la fatigue.",
            "prompt_type": "gratitude",
            "mood_score_at_entry": 4,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["text"] == "Aujourd'hui je me sens bien malgré la fatigue."
    assert data["prompt_type"] == "gratitude"

    r2 = await client.get("/api/v1/mental/journal", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert len(r2.json()) == 1


async def test_stress_techniques(client, db_session) -> None:
    email = "stress_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.get(
        "/api/v1/mental/stress-techniques",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    techniques = r.json()
    assert len(techniques) >= 3
    assert all("steps" in t for t in techniques)


async def test_stress_techniques_filtered_by_phase(client, db_session) -> None:
    email = "stress_phase@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.get(
        "/api/v1/mental/stress-techniques?phase=luteal",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    techniques = r.json()
    assert len(techniques) >= 1


async def test_mental_resources_public(client) -> None:
    token = await _register(client, "mental_res@example.com")
    r = await client.get("/api/v1/mental/resources", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    resources = r.json()
    assert len(resources) >= 2
    assert any(res["phone"] == "3114" for res in resources)


async def test_mental_alerts_empty(client) -> None:
    token = await _register(client, "alerts_empty@example.com")
    r = await client.get("/api/v1/mental/alerts", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []


# ── Intimate Health ────────────────────────────────────────────────────────


async def test_libido_requires_adult(client) -> None:
    token = await _register_teen(client, "teen_libido@example.com")
    r = await client.post(
        "/api/v1/intimate/libido",
        headers={"Authorization": f"Bearer {token}"},
        json={"log_date": str(date.today()), "score": 3},
    )
    assert r.status_code == 403


async def test_log_and_list_libido(client) -> None:
    token = await _register(client, "libido_adult@example.com")
    r = await client.post(
        "/api/v1/intimate/libido",
        headers={"Authorization": f"Bearer {token}"},
        json={"log_date": str(date.today()), "score": 4, "notes": "Phase ovulatoire, libido élevée"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["score"] == 4
    assert data["notes"] == "Phase ovulatoire, libido élevée"

    r2 = await client.get("/api/v1/intimate/libido", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert len(r2.json()) == 1


async def test_contraception_guide_accessible_to_all(client) -> None:
    token = await _register(client, "contra_guide@example.com")
    r = await client.get(
        "/api/v1/intimate/contraception-guide",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    methods = r.json()
    assert len(methods) >= 4
    ids = [m["id"] for m in methods]
    assert "pill" in ids
    assert "condom" in ids


async def test_sexual_education_teen_filtered(client) -> None:
    token = await _register_teen(client, "teen_sex_ed@example.com")
    r = await client.get(
        "/api/v1/intimate/sexual-education",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    content = r.json()
    assert all(c["age_group"] == "13+" for c in content)


async def test_sexual_education_adult_full(client) -> None:
    token = await _register(client, "adult_sex_ed@example.com")
    r = await client.get(
        "/api/v1/intimate/sexual-education",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    content = r.json()
    assert len(content) >= 4


async def test_intimate_health_log(client, db_session) -> None:
    email = "intimate_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/intimate/health-log",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "log_date": str(date.today()),
            "vaginal_dryness_severity": 2,
            "discharge_type": "normal_clear",
            "pain_during_intercourse": False,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["vaginal_dryness_severity"] == 2
    assert data["discharge_type"] == "normal_clear"


# ── Community ──────────────────────────────────────────────────────────────


async def test_post_requires_bloom(client) -> None:
    token = await _register(client, "post_free@example.com")
    r = await client.post(
        "/api/v1/community/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Mon titre", "body": "Mon contenu de post", "category": "cycle"},
    )
    assert r.status_code == 403


async def test_create_and_list_posts(client, db_session) -> None:
    email = "post_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/community/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Mon expérience avec le SPM",
            "body": "Je voulais partager mon expérience avec la communauté FlorNya...",
            "category": "cycle",
            "anonymous_display_name": "FleurAnonyme",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Mon expérience avec le SPM"
    assert data["anonymous_display_name"] == "FleurAnonyme"
    assert data["is_own"] is True

    r2 = await client.get("/api/v1/community/posts", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert len(r2.json()) >= 1


async def test_share_and_list_recipes(client, db_session) -> None:
    email = "recipe_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/community/recipes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Smoothie fer & énergie",
            "description": "Parfait pour la phase menstruelle",
            "ingredients": ["épinards", "banane", "graines de chanvre", "lait d'amande"],
            "phase": "menstrual",
            "cultural_cuisine": "africaine",
            "prep_time_minutes": 5,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Smoothie fer & énergie"
    assert data["phase"] == "menstrual"
    assert "épinards" in data["ingredients"]

    r2 = await client.get(
        "/api/v1/community/recipes?phase=menstrual",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    recipes = r2.json()
    assert len(recipes) >= 1
    assert all(rec["phase"] == "menstrual" for rec in recipes)


async def test_list_challenges(client, db_session) -> None:
    email = "challenges_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.get("/api/v1/community/challenges", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


# ── Chat ───────────────────────────────────────────────────────────────────


async def test_chat_requires_bloom(client) -> None:
    token = await _register(client, "chat_free@example.com")
    r = await client.post(
        "/api/v1/chat/message",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Bonjour Bloom !"},
    )
    assert r.status_code == 403


async def test_chat_message_bloom(client, db_session) -> None:
    email = "chat_bloom@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    r = await client.post(
        "/api/v1/chat/message",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Quels aliments recommandes-tu en phase lutéale ?"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "session_id" in data
    assert data["message"]["role"] == "user"
    assert data["reply"]["role"] == "assistant"
    assert len(data["reply"]["content"]) > 0

    session_id = data["session_id"]
    r2 = await client.post(
        "/api/v1/chat/message",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Et les suppléments ?", "session_id": session_id},
    )
    assert r2.status_code == 200
    assert r2.json()["session_id"] == session_id


async def test_list_chat_sessions(client, db_session) -> None:
    email = "chat_sessions@example.com"
    token = await _register(client, email)
    await _set_bloom(db_session, email)

    await client.post(
        "/api/v1/chat/message",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Bonjour"},
    )

    r = await client.get("/api/v1/chat/sessions", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    sessions = r.json()
    assert len(sessions) >= 1
    assert "session_id" in sessions[0]
    assert "preview" in sessions[0]


# ── Consultation ───────────────────────────────────────────────────────────


async def test_consultation_requires_bloom_pro(client) -> None:
    token = await _register(client, "consult_bloom@example.com")
    r = await client.post(
        "/api/v1/consultation/book",
        headers={"Authorization": f"Bearer {token}"},
        json={"scheduled_at": "2026-07-15T14:00:00Z"},
    )
    assert r.status_code == 403


async def test_book_consultation(client, db_session) -> None:
    email = "consult_pro@example.com"
    token = await _register(client, email)
    await _set_bloom_pro(db_session, email)

    r = await client.post(
        "/api/v1/consultation/book",
        headers={"Authorization": f"Bearer {token}"},
        json={"scheduled_at": "2026-07-15T14:00:00Z", "practitioner_name": "Dr. Sophie Martin"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "pending"
    assert data["practitioner_name"] == "Dr. Sophie Martin"

    r2 = await client.get("/api/v1/consultation/bookings", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert len(r2.json()) == 1


async def test_consultation_prep(client, db_session) -> None:
    email = "prep_pro@example.com"
    token = await _register(client, email)
    await _set_bloom_pro(db_session, email)

    r = await client.get("/api/v1/consultation/preparation", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "cycle_summary" in data
    assert "suggested_questions" in data
    assert len(data["suggested_questions"]) >= 3


async def test_support_info_bloom_pro(client, db_session) -> None:
    email = "support_pro@example.com"
    token = await _register(client, email)
    await _set_bloom_pro(db_session, email)

    r = await client.get("/api/v1/consultation/support-info", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["priority_queue"] is True
    assert data["response_time_hours"] == 2
