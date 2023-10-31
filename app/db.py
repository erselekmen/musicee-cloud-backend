from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, status, Depends, HTTPException
from pydantic import BaseModel

username = "erselekmen"
password = "VV4J5jV9&q*3XrY"
MONGO_INITDB_DATABASE = "users"
DATABASE_URL = "mongodb+srv://" + username + ":" + password + "@cluster0.eh8uyv7.mongodb.net/?retryWrites=true&w=majority"

app = FastAPI()

@app.lifespan("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(DATABASE_URL)
    app.mongodb = app.mongodb_client.users




"""
import pymongo
from pymongo import mongo_client

client = mongo_client.MongoClient(
    DATABASE_URL, serverSelectionTimeoutMS=5000)

try:
    conn = client.server_info()
    print(f'Connected to MongoDB {conn.get("version")}')
except Exception:
    print("Unable to connect to the MongoDB server.")

mongodb = client[MONGO_INITDB_DATABASE]
User = mongodb.users
User.create_index([("email", pymongo.ASCENDING)], unique=True)"""




"""
from fastapi import FastAPI, status, Depends, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient

username = "erselekmen"
password = "VV4J5jV9&q*3XrY"

DATABASE_URL = "mongodb+srv://"+username+":"+password+"@cluster0.eh8uyv7.mongodb.net/?retryWrites=true&w=majority"
database = None

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(DATABASE_URL)
    app.mongodb = app.mongodb_client.ItemDB
    """