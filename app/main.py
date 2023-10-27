from fastapi import FastAPI, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from app.db import *

SECRET_KEY = "83daa0256a228960fb23693bf1f6034d44396675749244721a2b20e896e11662"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = 15

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str or None = None

class User(BaseModel):
    username: str
    email: str or None = None
    full_name: str or None = None
    disabled: bool or None = None

class UserDB(User):
    hashed_password: str

class Item(BaseModel):
    song: str
    artist: str


pwd_context = CryptContext(schemes=["bcrypt"])
oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify (plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash (password)


async def get_user(username: str):
    user = await app.mongodb.items.find_one({"song": username})
    
    if user is not None:
        user_data = user
        return UserDB(**user_data)
    
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/create_user/", response_model=User)
async def create_user(user: User):
    existing_user = await app.mongodb.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Item already exists")
    await app.mongodb.users.insert_one(user.dict())
    return user

async def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    
    return user

async def create_access_token(data: dict, expires_delta: timedelta or None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)

    return encoded_jwt

async def get_current_user(token: str = Depends(oauth_2_scheme)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credential_exception
        
        token_data = TokenData(username = username)

    except JWTError:
        raise credential_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credential_exception
    
    return user

async def get_current_active_user(current_user: UserDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user

@app.post("/token", response_model = Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password!", headers={"WWW-Authenticate": "Bearer"})

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get ("/users/me/items")
async def read_own_items(current_user: User = Depends (get_current_active_user)):
    return [{"item_id": 1, "owner": current_user}]





"""
@app.post("/add_song/", response_model=Item)
async def create_item(item: Item):
    existing_item = await app.mongodb.items.find_one({"song": item.song})
    if existing_item:
        raise HTTPException(status_code=400, detail="Item already exists")
    await app.mongodb.items.insert_one(item.dict())
    return item

@app.get("/list_song/{item_name}", response_model=Item)
async def read_item(item_name: str):
    item = await app.mongodb.items.find_one({"song": item_name})
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
"""
