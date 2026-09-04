from app.main import app
async def _get_valid_api_key_and_auth(client, email="demouser@example.com"):
    await client.post(
        "/register",
        json={"username": "demouser", "email": email, "password": "StrongPass123!"},
    )
    login_response = await client.post(
        "/login", json={"email": email, "password": "StrongPass123!"}
    )
    token = login_response.json()["acess_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    key_response = await client.post("/generate_api_key", headers=auth_headers)
    raw_key = key_response.json()["api_key"]

    return raw_key, auth_headers


async def test_demo_success(
    client,
    db_session_fixture,
    redis_client
):
    app.state.write_request_log = False

    try:
        raw_key, auth_headers = await _get_valid_api_key_and_auth(client)

        headers = {"X-API-Key": raw_key}

        response = await client.get(
            "/demo",
            headers=headers
        )

        assert response.status_code == 200
        assert response.json() == {
            "message": "Request Successful"
        }

    finally:
        app.state.write_request_log = True

async def test_demo_missing_api_key_header(client, db_session_fixture):
    response = await client.get(
        "/demo",
        headers={}
    )
    assert response.status_code == 422


async def test_demo_invalid_api_key(client, db_session_fixture):
    headers = {"X-API-Key": "not-a-real-key-12345"}
    response = await client.get("/demo", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"


async def test_demo_rate_limit_exceeded(client, db_session_fixture, redis_client):
    app.state.write_request_log = False
    try:
        raw_key, auth_headers = await _get_valid_api_key_and_auth(client)
        headers = {"X-API-Key": raw_key}

        last_response = None
        for _ in range(101):
            last_response = await client.get("/demo", headers=headers)

        assert last_response.status_code == 429
        assert last_response.json()["detail"] == "Rate limit exceeded. Please try again later"
    finally:
            app.state.write_request_log = False

