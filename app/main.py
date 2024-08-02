from fastapi.exception_handlers import HTTPException
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from app.db import *
from app.schema import *
from app.utils import (
    get_hashed_password,
    create_access_token,
    create_refresh_token,
    verify_password
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL = "http://musicee.us-west-2.elasticbeanstalk.com"


@app.get("/api/health")
def root():
    return {"message": "Welcome to Musicee API V3"}


@app.post('/user/signup', summary="Create new user")
async def create_user(data: User):
    existing_username = await app.mongodb.users.find_one({"username": data.username})

    if existing_username:
        raise HTTPException(status_code=400, detail="Email or username already exists")

    user = {
        "username": data.username,
        "email": data.email,
        "password": get_hashed_password(data.password),
        "friends": [],
        "liked_songs": [],
        "liked_songs_date": [],
        "playlist": [],
        "comment": []
    }

    await app.mongodb.users.insert_one(user)

    return {
        "username": data.username,
        "email": data.email,
        "status": 200
    }


@app.post('/user/login', summary="Create access and refresh tokens for user")
async def login(data: UserLogin):
    user = await app.mongodb.users.find_one({"username": data.username})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    hashed_pass = user['password']
    if not verify_password(data.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    return {
        "access_token": create_access_token(user['email']),
        "refresh_token": create_refresh_token(user['email']),
    }


@app.get("/users/all", summary="Get all users")
async def get_all_users():
    users = app.mongodb.users.find({})

    if users:
        user_list = []
        async for document in users:
            del document['_id']
            user_list.append(document)
        return user_list
    else:
        raise HTTPException(status_code=404, detail="No users found in the database")


@app.get("/users/get_user_details/{username}", summary="List all user details")
async def get_user_details(username: str):
    user = await app.mongodb.users.find_one({"username": username})

    if user:
        return {
            "username": user["username"],
            "email": user["email"],
            "friends": user.get("friends", []),
            "liked_songs": user.get("liked_songs", []),
            "liked_songs_date": user.get("liked_songs_date", []),
            "playlist": user.get("playlist", []),
            "comment": user.get("comment", []),

        }

    else:
        raise HTTPException(status_code=404, detail=f"User with username {username} not found")

