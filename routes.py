from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Request, HTTPException
from typing import List, Union
from bson import ObjectId

from models import (
    BarakahValue,
    BarakahMindset,
    BarakahRitual,
    DailyItem,
    DailyBundle,
)

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


# response key -> (collection, name field on the document)
# The name field happens to equal the response key for all three collections.
DAILY_COLLECTIONS = {
    "value":   ("values",   "value"),
    "mindset": ("mindsets", "mindset"),
    "ritual":  ("rituals",  "ritual"),
}


@router.get("/daily", response_model=DailyBundle,
            response_description="A trio (value/mindset/ritual) that is stable for the whole day")
async def daily(request: Request, tz: str = "UTC"):
    # Resolve the caller's timezone (TRMNL passes trmnl.user.time_zone_iana).
    # Fall back to UTC for a missing/unknown zone instead of erroring.
    try:
        zone = ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError):
        zone = ZoneInfo("UTC")

    today = datetime.now(zone).date()
    ordinal = today.toordinal()  # day counter; +1 each calendar day

    items = {}
    for offset, (key, (collection, field)) in enumerate(DAILY_COLLECTIONS.items()):
        # Stable, deterministic ordering: ObjectIds sort by their bytes, so the
        # same day -> same index -> same document (no $sample randomness).
        cursor = request.app.state.mongodb[collection].find({}, {"_id": 1})
        ids = sorted([doc["_id"] async for doc in cursor])
        if not ids:
            raise HTTPException(status_code=404, detail=f"No documents in {collection}")

        # Distinct offset per collection so the three don't rotate in lockstep.
        idx = (ordinal + offset) % len(ids)
        doc = await request.app.state.mongodb[collection].find_one({"_id": ids[idx]})
        items[key] = DailyItem(
            name=doc[field],
            arabic=doc.get("arabic"),
            description=doc["description"],
        )

    return DailyBundle(date=today.isoformat(), **items)