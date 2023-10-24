from http.client import HTTPException
from fastapi import FastAPI
from app.db import get_database, close_database
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/items/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    existing_item = await app.mongodb.items.find_one({"name": item.name})
    if existing_item:
        raise HTTPException(status_code=400, detail="Item already exists")
    await app.mongodb.items.insert_one(item.dict())
    return item

@app.get("/items/{item_name}", response_model=Item)
async def read_item(item_name: str):
    item = await app.mongodb.items.find_one({"name": item_name})
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

