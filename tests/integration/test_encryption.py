from datetime import date

from sqlalchemy import select

from app.models.mood_log import MoodLog


async def test_journal_text_encrypted_in_db(client, db_session) -> None:
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "a@example.com",
            "password": "password123",
            "date_of_birth": "1995-01-01",
            "language": "fr",
        },
    )
    assert register.status_code == 200
    access = register.json()["access_token"]

    from app.models.user import User, UserPlan

    result_u = await db_session.execute(select(User).where(User.email == "a@example.com"))
    user = result_u.scalar_one()
    user.plan = UserPlan.essential
    await db_session.commit()

    mood_resp = await client.post(
        "/api/v1/mental/mood",
        headers={"Authorization": f"Bearer {access}"},
        json={"log_date": str(date.today()), "mood_score": 3, "journal_text": "secret"},
    )
    assert mood_resp.status_code == 200
    assert mood_resp.json()["journal_text"] == "secret"

    result = await db_session.execute(select(MoodLog))
    mood = result.scalars().first()
    assert mood is not None
    assert mood.journal_text_encrypted is not None
    assert mood.journal_text_encrypted != "secret"
