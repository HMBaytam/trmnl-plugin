from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import List
from bson import ObjectId

from models import BarakahCard

router = APIRouter()

@router.get("/values", response_description="List of all Barakah Values", response_model=List[BarakahCard])
async def list_values(request: Request):
    values = list( request.app.mongodb["values"].find(limit=100))
    return values

@router.get("/value/{id}", response_description="Get a single Barakah Value", response_model=BarakahCard)
async def find_value(id: str, request: Request):
    if (value := request.app.mongodb["values"].find_one({"_id": ObjectId(id)})) is not None:
        return value

    raise HTTPException(status_code=404, detail=f"Value {id} not found")

@router.get("/mindsets", response_description="List of all Barakah Values", response_model=List[BarakahCard])
async def list_values(request: Request):
    values = list( request.app.mongodb["mindsets"].find(limit=100))
    return values

@router.get("/mindset/{id}", response_description="Get a single Barakah Value", response_model=BarakahCard)
async def find_value(id: str, request: Request):
    if (value := request.app.mongodb["mindsets"].find_one({"_id": ObjectId(id)})) is not None:
        return value

    raise HTTPException(status_code=404, detail=f"Value {id} not found")

@router.get("/rituals", response_description="List of all Barakah Values", response_model=List[BarakahCard])
async def list_values(request: Request):
    values = list( request.app.mongodb["rituals"].find(limit=100))
    return values

@router.get("/ritual/{id}", response_description="Get a single Barakah Value", response_model=BarakahCard)
async def find_value(id: str, request: Request):
    if (value := request.app.mongodb["rituals"].find_one({"_id": ObjectId(id)})) is not None:
        return value

    raise HTTPException(status_code=404, detail=f"Value {id} not found")