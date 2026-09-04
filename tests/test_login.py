import pytest


async def test_login_success(client, db_session_fixture):

    register_payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "StrongPass123!",
    }

    reg_response = await client.post("/register", json=register_payload)
    assert reg_response.status_code == 201

    login_payload = {
         "email":"alice@example.com",
          "password":"StrongPass123!",
            }


    response = await client.post("/login", json=login_payload)

    assert response.status_code == 200
    body = response.json() 

    assert body["message"] == "User login succcess"
    assert body["token_type"] == "bearer"
    assert "acess_token" in body and body["acess_token"]


async def test_login_nonexistent_email(client, db_session_fixture):
    payload = {
        "email": "random@example.com",
        "password":"StrongPass1231"
    }

    response = await client.post("/login", json = payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


async def test_login_wrong_password(client, db_session_fixture):
    register_payload = {
        "username": "bob",
        "email": "bob@example.com",
        "password": "StrongPass123!",
    }

    reg_response = await client.post("/register", json=register_payload)
    assert reg_response.status_code == 201

    login_payload = {
        "email": "bob@example.com",
        "password": "WrongPassword999",
    }

    response = await client.post("/login", json=login_payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

@pytest.mark.parametrize(
    "bad_payload",
    [
        {"email": "x@example.com"},
        {"password":"StrongPass123!"}
        
    ]
)

async def test_login_missing_fields(client, bad_payload):
    response = await client.post("/login", json=bad_payload)
    assert response.status_code == 422 

