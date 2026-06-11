from fastapi import APIRouter, Request, HTTPException
from typing import List
from bson import ObjectId

from models import BarakahCard

router = APIRouter()

def register_collection(*, collection: str, list_path: str, item_path: str, label: str):
    @router.get(list_path, response_model=List[BarakahCard],
                response_description=f"List of all {label}s")
    async def list_items(request: Request):
        return list(request.app.mongodb[collection].find(limit=100))

    @router.get(item_path, response_model=BarakahCard,
                response_description=f"Get a single {label}")
    async def find_item(id: str, request: Request):
        if (item := request.app.mongodb[collection].find_one({"_id": ObjectId(id)})) is not None:
            return item
        raise HTTPException(status_code=404, detail=f"{label} {id} not found")

register_collection(collection="values",   list_path="/values",   item_path="/value/{id}",   label="Value")
register_collection(collection="mindsets", list_path="/mindsets", item_path="/mindset/{id}", label="Mindset")
register_collection(collection="rituals",  list_path="/rituals",  item_path="/ritual/{id}",  label="Ritual")
