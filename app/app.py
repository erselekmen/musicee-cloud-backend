from fastapi import FastAPI
from app.db import get_database, close_database

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await get_database()

@app.on_event("shutdown")
async def shutdown_event():
    await close_database()

@app.get("/")
async def read_root():
    return {"Hello": "World"}
