import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import AsyncMongoClient

from config import settings
from routes import router as api_router

# Reuse uvicorn's logger so app logs share its handler/format and go to stdout
# (no extra root handler -> no duplicate lines).
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(settings.mongodb_uri)
    app.state.mongodb = client[settings.mongodb]
    yield
    await client.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(api_router, prefix="/barakah")
