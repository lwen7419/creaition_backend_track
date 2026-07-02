import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.cache import get_redis
from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def _shared_fake_redis():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture()
def redis_client(_shared_fake_redis):
    _shared_fake_redis.flushall()
    return _shared_fake_redis


@pytest.fixture()
def client(db_session, redis_client):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: redis_client
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
