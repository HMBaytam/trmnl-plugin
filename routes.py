from fastapi import APIRouter, Request, HTTPException
from typing import List, Union
from bson import ObjectId

from models import BarakahValue, BarakahMindset, BarakahRitual

router = APIRouter()

COLLECTIONS = ["values", "mindsets", "rituals"]
BarakahAny = Union[BarakahValue, BarakahMindset, BarakahRitual]

def register_collection(*, collection: str, list_path: str, item_path: str, label: str, model):
    @router.get(list_path, response_model=List[str],
                response_description=f"List of all {label}s ids")
    async def list_ids(request: Request):
        cursor = request.app.state.mongodb[collection].find({}, {"_id": 1}, limit=100)
        return [str(doc["_id"]) async for doc in cursor]

    @router.get(item_path, response_model=model,
                response_description=f"Get a single {label}")
    async def find_item(id: str, request: Request):
        if (item := await request.app.state.mongodb[collection].find_one({"_id": ObjectId(id)})) is not None:
            return item
        raise HTTPException(status_code=404, detail=f"{label} {id} not found")

register_collection(collection="values",   list_path="/values",   item_path="/value/{id}",   label="Value",   model=BarakahValue)
register_collection(collection="mindsets", list_path="/mindsets", item_path="/mindset/{id}", label="Mindset", model=BarakahMindset)
register_collection(collection="rituals",  list_path="/rituals",  item_path="/ritual/{id}",  label="Ritual",  model=BarakahRitual)



@router.get("/random", response_model=List[BarakahAny],
            response_description="One random document from each collection")
async def random_bundle(request: Request):
    bundle = []
    for collection in COLLECTIONS:
        cursor = await request.app.state.mongodb[collection].aggregate([{"$sample": {"size": 1}}])
        docs = await cursor.to_list(length=1)
        if not docs:
            raise HTTPException(status_code=404, detail=f"No documents in {collection}")
        bundle.append(docs[0])
    return bundle