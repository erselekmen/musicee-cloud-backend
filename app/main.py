from fastapi import HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.db import app, get_mysql_connection
from app.schema import User, UserLogin
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


@app.get("/api/health")
def root():
    return {"message": "Welcome to Musicee API V3"}


@app.post('/user/signup', summary="Create new user")
async def create_user(data: User):
    connection = await get_mysql_connection()

    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM users WHERE username=%s OR email=%s", (data.username, data.email))
        existing_user = await cursor.fetchone()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email or username already exists")

    user = {
        "username": data.username,
        "email": data.email,
        "password": get_hashed_password(data.password)
    }

    async with connection.cursor() as cursor:
        await cursor.execute(
            "INSERT INTO users (username, email, password) "
            "VALUES (%s, %s, %s)",
            (user["username"], user["email"], user["password"])
        )

    return {
        "username": data.username,
        "email": data.email,
        "status": 200
    }


@app.post('/user/login', summary="Create access and refresh tokens for user")
async def login(data: UserLogin):
    connection = await get_mysql_connection()
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM users WHERE username=%s", (data.username,))
        user = await cursor.fetchone()

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
    connection = await get_mysql_connection()
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM users")
        users = await cursor.fetchall()

    if users:
        user_list = []
        for user in users:
            user_list.append({
                "username": user["username"],
                "email": user["email"]
            })
        return user_list
    else:
        raise HTTPException(status_code=404, detail="No users found in the database")


@app.get("/users/get_user_details/{username}", summary="List all user details")
async def get_user_details(username: str):
    connection = await get_mysql_connection()
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = await cursor.fetchone()

    if user:
        return {
            "username": user["username"],
            "email": user["email"]        }
    else:
        raise HTTPException(status_code=404, detail=f"User with username {username} not found")

