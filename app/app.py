from http.client import HTTPException
from fastapi import FastAPI
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

DATABASE_URL = "mongodb+srv://erselekmen:VV4J5jV9&q*3XrY@cluster0.eh8uyv7.mongodb.net/?retryWrites=true&w=majority"  # Using the Docker service name `mongo`
database = None

app = FastAPI()
class Item(BaseModel):
    name: str
    description: str

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(DATABASE_URL)
    app.mongodb = app.mongodb_client.ItemDB

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/items/", response_model=Item)
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

