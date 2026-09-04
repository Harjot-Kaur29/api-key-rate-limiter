import pytest
import pytest_asyncio
import redis.asyncio as redis

from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db
from dependencies import get_redis
from app.db.base import Base


# =========================================================
# TEST DATABASE — SQLITE
# =========================================================

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


# =========================================================
# CREATE SQLITE TABLES
# =========================================================

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


# =========================================================
# DATABASE SESSION
# =========================================================

@pytest.fixture()
def db_session_fixture():

    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# =========================================================
# REDIS TEST DATABASE
# =========================================================

@pytest_asyncio.fixture()
async def redis_client():

    client = redis.from_url(
        "redis://localhost:6379/15"
    )

    await client.flushdb()

    yield client

    await client.flushdb()
    await client.aclose()


# =========================================================
# AUTH HEADER
# =========================================================

@pytest_asyncio.fixture()
async def auth_headers(client):

    await client.post(
        "/register",
        json={
            "username": "authuser",
            "email": "authuser@example.com",
            "password": "StrongPass123!",
        },
    )

    login_response = await client.post(
        "/login",
        json={
            "email": "authuser@example.com",
            "password": "StrongPass123!",
        },
    )

    token = login_response.json()["acess_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


# =========================================================
# HTTP CLIENT
# =========================================================

@pytest_asyncio.fixture()
async def client(db_session_fixture, redis_client):

    def override_get_db():
        yield db_session_fixture

    def override_get_redis():
        return redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()