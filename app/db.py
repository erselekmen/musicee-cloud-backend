from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

DATABASE_URL = "mongodb+srv://erselekmen:VV4J5jV9&q*3XrY@cluster0.eh8uyv7.mongodb.net/?retryWrites=true&w=majority"  # Using the Docker service name `mongo`
database = None

class Item(BaseModel):
    name: str
    description: str

async def get_database():
    global database
    client = AsyncIOMotorClient(DATABASE_URL)
    database = client.mydatabase  # Use your desired database name here

async def close_database():
    database.client.close()