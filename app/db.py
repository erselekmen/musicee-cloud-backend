from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI

username = "erselekmen"
password = "VV4J5jV9&q*3XrY"
MONGO_INITDB_DATABASE = "users"
DATABASE_URL = "mongodb+srv://" + username + ":" + password + "@cluster0.eh8uyv7.mongodb.net/?retryWrites=true&w=majority"

app = FastAPI()


@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(DATABASE_URL)
    app.mongodb = app.mongodb_client.musicee_db
