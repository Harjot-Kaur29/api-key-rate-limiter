
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis.asyncio as redis
from app.main import app
from app.db.session import get_db
from dependencies import get_redis
from app.models.user import Base  # adjust: Base may live in app/db/base.py etc.
 
# ---- SQLite in-memory: zero setup, no external service needed ----
# StaticPool + check_same_thread=False is required so the SAME in-memory
# DB is shared across the multiple connections a test can open, instead
# of each connection getting its own empty in-memory DB.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
 
@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    """Create all tables once at the start of the test session, drop at the end."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
 
 
@pytest.fixture()
def db_session():
    """
    A fresh DB session per test, wrapped in a transaction that's rolled back
    after the test — so tests never leak data into each other.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
 
    yield session
 
    session.close()
    transaction.rollback()
    connection.close()



@pytest_asyncio.fixture()
async def redis_client():
    client = redis.from_url("redis://localhost:6379/15")
    await client.flushdb()       # clean slate before the test
    yield client
    await client.flushdb()       # clean up after the test
    await client.aclose()

@pytest_asyncio.fixture()
async def auth_headers(client):
    """Registers a user, logs in, returns headers with a valid Bearer token."""
    await client.post("/register", json={
        "username": "authuser",
        "email": "authuser@example.com",
        "password": "StrongPass123!",
    })
    login_response = await client.post("/login", json={
        "email": "authuser@example.com",
        "password": "StrongPass123!",
    })
    token = login_response.json()["acess_token"]  # matches your route's typo
    return {"Authorization": f"Bearer {token}"}
 
@pytest_asyncio.fixture()
async def client(db_session, redis_client):
    """
    Async test client wired to the FastAPI app, with get_db overridden
    to use our transactional test session instead of the real one.
    """
 
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # cleanup handled by db_session fixture itself

    def override_get_redis():
        return redis_client
 
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
 
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
 
    app.dependency_overrides.clear()