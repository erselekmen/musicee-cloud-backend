from fastapi.exception_handlers import HTTPException
from fastapi import Depends, status
from pymongo import ReturnDocument
from app.db import *
from app.schema import *
from app.utils import (
    get_hashed_password,
    create_access_token,
    create_refresh_token,
    verify_password
)


@app.post('/user/signup', summary="Create new user")
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


@app.post('/user/login', summary="Create access and refresh tokens for user")
async def login(data: User):
    user = await app.mongodb.users.find_one({"email": data.email})
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


@app.get('/tracks/get_tracks', summary="List all tracks")
async def get_tracks():
    cursor = app.mongodb.tracks.find({})

    if cursor is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No track was found!"
        )

    tracks = []
    async for document in cursor:
        del document['_id']
        tracks.append(document)

    return tracks


@app.post("/tracks/add_track", summary="Add a track")
async def add_track(data: Track):
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please check track information!"
        )

    track = {
        "track_name": data.track_name,
        "track_artist": data.track_artist,
        "track_album": data.track_album,
        "track_rating": data.track_rating,
        "track_id": data.track_id,
        "track_release_year": data.track_release_year
    }

    await app.mongodb.tracks.insert_one(track)

    return {"message": "Track added successfully."}


@app.put("/tracks/update_track/{track_id}", summary="Update track")
async def update_track(data: Track, track_id: int):
    await app.mongodb.tracks.find_one_and_update(
        {"track_id": track_id},
        {"$set":
            {
                "track_name": data.track_name,
                "track_artist": data.track_artist,
                "track_album": data.track_album,
                "track_rating": data.track_rating,
                "track_release_year": data.track_release_year
            }
        },
        return_document=ReturnDocument.AFTER
    )

    return {"message": f"Track with ID {track_id} has been updated."}


@app.delete("/tracks/delete_track/{track_id}", summary="Delete track")
async def delete_track(track_id: int):
    track = await app.mongodb.tracks.find_one({"track_id": track_id})

    if track:

        await app.mongodb.tracks.delete_one({"track_id": track_id})
        return {"message": f"Track with ID {track_id} has been deleted."}

    else:
        return {"message": f"Track with ID {track_id} does not exist."}


@app.post("/tracks/get_track_name/{track_id}", summary="Get track name by ID", response_model=str)
async def get_track_name(track_id: int):
    track = await app.mongodb.tracks.find_one({"track_id": track_id}, {"track_name": 1})

    if track and "track_name" in track:
        return track["track_name"]
    else:
        raise HTTPException(status_code=404, detail=f"Track with ID {track_id} not found")


@app.post("/tracks/get_song_details",summary="Get Details",response_model=Track)
async def get_details(track_id: int):
    track = await app.mongodb.tracks.find_one({"track_id": track_id})
    if track:
        return track
    else:
        return {"message": f"Track with ID {track_id} does not exist."}