from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import dotenv_values
from pymongo import AsyncMongoClient
from routes import router as api_router

config = dotenv_values(".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(config["MONGODB_URI"])
    app.state.mongodb = client[config["MONGODB"]]
    yield
    await client.close()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router, prefix="/api")
