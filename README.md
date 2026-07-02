# Creaition AI/LLM Development

Task management API with LLM-powered features (natural language task creation, tag suggestions, priority recommendations) on top of a standard CRUD backend.

## Tech stack

- FastAPI + SQLAlchemy + SQLite
- Pydantic for request/response validation
- Redis (via `redis`/`fakeredis`) for list-endpoint caching
- Anthropic API for LLM features
- ChromaDB for embeddings
- pytest + httpx `TestClient` for testing

## Project structure

```
.
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── src/
│   ├── main.py          # FastAPI app + router registration
│   ├── config.py        # Settings (env-driven)
│   ├── database.py      # SQLAlchemy engine/session
│   ├── cache.py         # Redis client + cache key/invalidation helpers
│   ├── models/           # SQLAlchemy ORM models
│   ├── routes/           # FastAPI routers (path + handler logic)
│   ├── schemas/          # Pydantic request/response schemas
│   ├── services/         # Business logic, DB queries, LLM/embedding wrappers
│   └── utils/             # Small shared helpers
├── tests/
└── docs/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in ANTHROPIC_API_KEY
```

## Run

```bash
uvicorn src.main:app --reload
```

API docs: http://localhost:8000/docs

## Test

```bash
pytest
```

Tests run fully offline — the DB, Redis, and Anthropic clients are all faked/overridden via dependency injection (see `tests/conftest.py`), so no network access or API key is required.

## Docs

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — architecture diagram, scaling notes, and design trade-offs.
- [CLAUDE.md](CLAUDE.md) — project context and conventions for AI-assisted development.
