from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import FastAPI, status, Depends, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from app.db import *


class Item(BaseModel):
    song: str
    artist: str

@app.post("/add_song/", response_model=Item)
async def create_item(item: Item):
    existing_item = await app.mongodb.items.find_one({"song": item.song})
    if existing_item:
        raise HTTPException(status_code=400, detail="Item already exists")
    await app.mongodb.items.insert_one(item.dict())
    return item

@app.get("/list_song/{item_name}", response_model=Item)
async def read_item(item_name: str):
    item = await app.mongodb.items.find_one({"song": item_name})
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
