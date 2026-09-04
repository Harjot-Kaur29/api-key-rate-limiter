import pytest
from app.models.user import User

async def test_register_success(client, db_session_fixture):
    payload = {
        "username":"alice",
        "email":"alice@example.com",
        "password":"StrongPass123!",
    }

    response = await client.post("/register", json=payload)

    # Check the HTTP-level contract
    assert response.status_code == 201
    assert response.json() == {"message": "User registered successfully"}


    #Check the actual DB side effect, not just the response.
    
    user = db_session_fixture.query(User).filter(User.email == "alice@example.com").first()

    assert user is not None
    assert user.username == "alice"

    # Never assert the password is stored as-is. Confirm it's hashed

    assert user.hashed_password != "StrongPass123!"


async def test_register_duplicate_email(client, db_session_fixture):
    payload = {
        "username" : "bob",
        "email": "bob@example.com",
        "password" : "StrongPass123!",
    }

    first = await client.post("/register", json=payload)
    assert first.status_code == 201

    #same email different username - should get rejected

    second = await client.post(
        "/register",
        json = {**payload, "username": "bob2"},
    )

    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"

    #Confirm only One row exists 

    count = db_session_fixture.query(User).filter(User.email == "bob@example.com").count()
    assert count == 1


@pytest.mark.parametrize(
    "bad_payload",
    [
        ({"email": "x@example.com", "password": "StrongPass123!"}, "username"),
        ({"username":"x", "password": "StrongPass123!"}, "email"),
        ({"username": "x", "email": "x@example.com"}, "password"),
    ]
)

async def test_register_missing_fields(client, bad_payload):
    response = await client.post("/register", json=bad_payload)
    assert response.status_code == 422 
    
