from datetime import date, timedelta


async def test_auth_users_cycle_flow(client) -> None:
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "b@example.com",
            "password": "password123",
            "date_of_birth": "1990-01-01",
            "language": "fr",
        },
    )
    assert register.status_code == 200
    access = register.json()["access_token"]

    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["email"] == "b@example.com"

    period_start = date.today() - timedelta(days=10)
    rec = await client.post(
        "/api/v1/cycle/records",
        headers={"Authorization": f"Bearer {access}"},
        json={"period_start": str(period_start), "cycle_length": 28, "notes": "note"},
    )
    assert rec.status_code == 200
    assert rec.json()["notes"] == "note"

    current = await client.get("/api/v1/cycle/current", headers={"Authorization": f"Bearer {access}"})
    assert current.status_code == 200
    assert current.json()["last_period_start"] == str(period_start)
