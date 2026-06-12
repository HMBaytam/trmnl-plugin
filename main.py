import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import AsyncMongoClient

from config import settings
from barakah import router as barakah_router

# Reuse uvicorn's logger so app logs share its handler/format and go to stdout
# (no extra root handler -> no duplicate lines).
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(settings.mongodb_uri)
    app.state.mongodb = client[settings.mongodb]
    yield
    await client.close()


tags_metadata = [
    {
        "name": "General",
        "description": "Service-level endpoints such as health checks.",
    },
    {
        "name": "Barakah Cards",
        "description": "Browse and fetch Barakah values, mindsets, and rituals.",
    },
]

app = FastAPI(lifespan=lifespan, openapi_tags=tags_metadata)


@app.get("/health", tags=["General"])
async def health():
    return {"status": "ok"}


app.include_router(barakah_router, prefix="/barakah", tags=["Barakah Cards"])
