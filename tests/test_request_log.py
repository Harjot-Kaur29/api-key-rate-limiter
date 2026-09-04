from app.models.user import User
from app.models.api_key import APIKey
from app.models.request_log import RequestLog


def test_write_request_log(db_session_fixture):

    # 1. Create a test user
    user = User(
        username="logtestuser",
        email="logtest@example.com",
        hashed_password="test-password",
    )

    db_session_fixture.add(user)
    db_session_fixture.commit()
    db_session_fixture.refresh(user)

    # 2. Create a test API key belonging to that user
    api_key = APIKey(
        user_id=user.id,
        hashed_key="test-hashed-key",
        is_active=True,
    )

    db_session_fixture.add(api_key)
    db_session_fixture.commit()
    db_session_fixture.refresh(api_key)

    # 3. Create request log
    log = RequestLog(
        user_id=user.id,
        api_key_id=api_key.id,
        status_code=200,
    )

    db_session_fixture.add(log)
    db_session_fixture.commit()
    db_session_fixture.refresh(log)

    # 4. Verify it was inserted
    assert log.id is not None
    assert log.user_id == user.id
    assert log.api_key_id == api_key.id
    assert log.status_code == 200