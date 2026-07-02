import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.cache import get_redis
from app.database import Base, get_db
from app.main import app
from app.services.llm_service import get_llm_service

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


class FakeLLMService:
    def __init__(self):
        self.extracted: dict = {}
        self.suggested_tags: list[str] = []
        self.recommended_priority: str = "medium"
        self.last_call: dict | None = None

    def extract_task(self, text, *, reference_date):
        self.last_call = {"text": text, "reference_date": reference_date}
        return self.extracted

    def suggest_tags(self, title, description=None):
        self.last_call = {"title": title, "description": description}
        return self.suggested_tags

    def recommend_priority(self, title, description=None):
        self.last_call = {"title": title, "description": description}
        return self.recommended_priority


@pytest.fixture()
def fake_llm_service():
    return FakeLLMService()


@pytest.fixture()
def client(db_session, redis_client, fake_llm_service):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: redis_client
    app.dependency_overrides[get_llm_service] = lambda: fake_llm_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
