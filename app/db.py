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