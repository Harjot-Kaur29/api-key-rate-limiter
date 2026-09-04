import pytest
from app.models.api_key import APIKey


async def test_generate_api_key_first_time(client,db_session_fixture,auth_headers):
    response = await client.post("/generate_api_key", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert "api_key" in body and body["api_key"]

    keys = db_session_fixture.query(APIKey).all()
    assert len(keys) == 1
    assert keys[0].is_active is True




async def test_generate_key_rotation(client,db_session_fixture, auth_headers):
    first_response = await client.post("/generate_api_key", headers = auth_headers)
    first_key_value = first_response.json()["api_key"]

    second_response = await client.post("/generate_api_key", headers = auth_headers)
    second_key_value = second_response.json()["api_key"]


    assert first_key_value != second_key_value

    keys = db_session_fixture.query(APIKey).all()
    assert len(keys) == 2

    active_keys = [k for k in keys if k.is_active is True]
    inactive_keys = [k for k in keys if k.is_active is False]

    assert len(active_keys) == 1
    assert len(inactive_keys) == 1


async def test_generate_api_key_no_auth_header(client,db_session_fixture):
    response = await client.post("/generate_api_key")
    assert response.status_code == 422

    assert db_session_fixture.query(APIKey).count() == 0


async def test_generate_api_key_two_users_dont_interfere(client,db_session_fixture):

    await client.post(
        "/register",
        json = {"username":"userA", "email": "userA@example.com", "password": "StrongPass123!"},
    )

    login_a = await client.post(
        "/login", json={"email": "userA@example.com", "password":"StrongPass123!"}
    )

    headers_a = {"Authorization": f"Bearer {login_a.json()['acess_token']}"}
    await client.post("/generate_api_key", headers = headers_a)

    await client.post(
        "/register",
        json = {"username":"userB", "email": "userB@example.com", "password": "StrongPass123!"},
    )

    login_b = await client.post(
            "/login", json={"email": "userB@example.com", "password":"StrongPass123!"}
        )
    headers_b = {"Authorization": f"Bearer {login_b.json()['acess_token']}"}
    response_b = await client.post("/generate_api_key", headers = headers_b)

    assert response_b.status_code == 200

    await client.post("/generate_api_key", headers = headers_a)

    active_keys = [k for k in db_session_fixture.query(APIKey).all() if k.is_active is True]
    assert len(active_keys) == 2

    b_user = db_session_fixture.query(APIKey).filter(APIKey.user_id == 2).first()
    

                                            