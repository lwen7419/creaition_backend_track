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
└── 
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

## Design choices

1. I decided to choose prompting over a sklearn classifier for priority recommendation in Schemas because a sklearn classifier needs labeled trianing examples, but currently there is no historical task data with priority labels.
2. I chose tool calling (Anthropic API) rather than free-text parsing for extraction for reliability.
3. Similarly, I chose ChromaDB's local embedder rather than writing my own embedder or the one I wrote for my project at Alibaba International, since the latter would require Ollama locally downloaded, more setup for user. ChromaDB is also better on latency although maybe not accuracy, but task-management is a high-frequency AI usage example that expects low friction results. Furthermore, for this tool, it would likely be a side feature of cre(ai)tion, and less latency means more time spent on the main features. 

### Challenges and Solutions

Halfway through the tasks for backend development track, I realized that I was more familiar and comfortable with the assignment details associated with the ai/llm development track, as I had more experiences implementing RAG pipelines than I have with CRUD API building. Although I have already spent around two hours on the previous track, I have another two hours left on the time limit, enough for me to implement the ai/llm tasks on top of the CRUD API layer I already have. I have left previous commit history for viewing.

## Known limitations
1. ChromaDB's local embedder is not optmized for task-related AI. Perhaps it is currently chosen to prioritize speed, but a customized embedder might take speed and accuracy.
2. Although prompting Anthropic is best current choice for priority recommendation, it has per-call cost and latency drawbacks that can be improved with more time and labeled dataset.
3. Most current code is written by ClaudeCode although briefly proofread by me because of drawbacks in time. Hence, code style is probably not coherent.
4. CLAUDE.md has unneeded information.
5. LLM-backed GET is not cached, more latency and cost via Anthropic API.
6. Task breakdown mentioned as the other AI feature is unbuilt, abandoned for time scrunch.  

## Future improvements
1. With more time, I will write my own embedder, and I have experience doing and am confident such task will be done well.
2. With a labeled dataset and time on my hands, I can train my own sklearn classifier for priority reccomendation.
3. Coherent code style and documentation
4. Better commit messages
5. CLAUDE.md made more concise and precise.
6. Cache GETs.
7. Add task breakdown feature.

## Docs

- [CLAUDE.md](CLAUDE.md) — project context and conventions for AI-assisted development.
