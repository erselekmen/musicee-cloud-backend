from fastapi.exception_handlers import HTTPException
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.db import *
from app.schema import *
from app.utils import (
    get_hashed_password,
    create_access_token,
    create_refresh_token,
    verify_password
)


@app.post('/signup', summary="Create a new user")
async def create_user(data: User):
    # querying database to check if user already exist
    existing_user = await app.mongodb.users.find_one({"email": data.email})

    if existing_user:
        raise HTTPException(status_code=400, detail="Item already exists")

    user = {
        "email": data.email,
        "password": get_hashed_password(data.password)
    }

    await app.mongodb.users.insert_one(user)
    return {
        "email": data.email,
        "status": 200
    }


@app.post('/login', summary="Create access and refresh tokens for user")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await app.mongodb.users.find_one({"email": form_data.username})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    hashed_pass = user['password']
    if not verify_password(form_data.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    return {
        "access_token": create_access_token(user['email']),
        "refresh_token": create_refresh_token(user['email']),
    }

tracks = []
@app.post("/tracks")
async def add_track(track: Track):
    global tracks
    tracks.append(track)
    return {"message": "Track added successfully."}
@app.put("/tracks/{track_id}")
async def update_track(track_id: int, updated_feature: str):
    global tracks
    for track in tracks:
        if track.track_id == track_id:
            # Update the track's feature
            track.track_name = updated_feature
            return {"message": f"Track with ID {track_id} has been updated."}
    return {"error": f"Track with ID {track_id} not found."}
@app.delete("/tracks/{track_id}")
async def delete_track(track_id: int):
    global tracks
    for track in tracks:
        if track.track_id == track_id:
            tracks.remove(track)
            return {"message": f"Track with ID {track_id} has been deleted."}
    raise HTTPException(status_code=404, detail=f"Track with ID {track_id} not found.")
@app.get("/tracks")
async def get_tracks():
    return tracks


"""@app.post("/create_user/", response_model=User)
async def create_user(user: User):
    existing_user = await app.mongodb.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Item already exists")
    await app.mongodb.users.insert_one(user.dict())
    return user"""

"""
pwd = get_password_hash("ersel123")
print(pwd)
"""

"""class Item(BaseModel):
    song: str
    artist: str"""

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
