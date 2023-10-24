from motor.motor_asyncio import AsyncIOMotorClient

DATABASE_URL = "mongodb://mongo:27017"  # Using the Docker service name `mongo`
database = None

async def get_database():
    global database
    client = AsyncIOMotorClient(DATABASE_URL)
    database = client.mydatabase  # Use your desired database name here

async def close_database():
    database.client.close()