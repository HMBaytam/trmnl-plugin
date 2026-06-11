from fastapi import FastAPI
from dotenv import dotenv_values
from pymongo import MongoClient
from routes import router as api_router
config = dotenv_values(".env")
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    app.mongodb_client = MongoClient(config["MONGODB_URI"])
    app.mongodb = app.mongodb_client[config["MONGODB"]]

@app.on_event("shutdown")
async def shutdown_event():
    app.mongodb_client.close()

app.include_router(api_router, prefix="/api")



