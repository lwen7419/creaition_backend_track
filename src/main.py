from fastapi import FastAPI

from src.database import Base, engine
from src.routes import health, items, tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Creaition Backend")

app.include_router(health.router)
app.include_router(items.router)
app.include_router(tasks.router)
