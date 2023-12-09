from fastapi.exception_handlers import HTTPException
from fastapi import Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pymongo import ReturnDocument
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


@app.get("/api/health")
def root():
    return {"message": "Welcome to Musicee API"}


@app.post('/user/signup', summary="Create new user")
async def create_user(data: User):
    # querying database to check if user already exist
    existing_email = await app.mongodb.users.find_one({"email": data.email})
    existing_username = await app.mongodb.users.find_one({"username": data.username})

    if existing_email or existing_username:
        raise HTTPException(status_code=400, detail="Email or username already exists")

    user = {
        "username": data.username,
        "email": data.email,
        "password": get_hashed_password(data.password),
        "friends": [],
        "favorite_songs": [],
        "liked_songs": []
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



async def get_user_by_username(username: str):
    user = await app.mongodb.users.find_one({"username": username})
    return user



async def update_user_details(username: str, friends_list: list):
    await app.mongodb.users.update_one(
        {"username": username},
        {"$set": {"friends": friends_list}}
    )


@app.put("/users/add_friend/{username}/{friend_username}", summary="Add friend by username")
async def add_friend(username: str, friend_username: str):
    user = await get_user_by_username(username)
    friend = await get_user_by_username(friend_username)

    if user and friend:
        if friend_username not in user.get("friends", []):
            user_friends = user.get("friends", [])
            user_friends.append(friend_username)
            await update_user_details(username, user_friends)
            return {"message": f"User '{username}' added '{friend_username}' as a friend."}
        else:
            raise HTTPException(status_code=400,
                                detail=f"'{friend_username}' is already in the friend list of '{username}'.")
    else:
        raise HTTPException(status_code=404, detail="User or friend not found.")


@app.get("/users/list_friends/{username}", summary="List all friends of a user")
async def get_friends(username: str):
    user = await app.mongodb.users.find_one({"username": username})

    if user:
        return user.get("friends", [])
    else:
        raise HTTPException(status_code=404, detail=f"User with username {username} not found")


@app.get("/users/get_user_details/{username}", summary="List all user details")
async def get_user_details(username: str):
    user = await app.mongodb.users.find_one({"username": username})

    if user:
        return {
            "username": user["username"],
            "email": user["email"],
            "friends": user.get("friends", []),
            "favorite_songs": user.get("favorite_songs", []),
            "liked_songs": user.get("liked_songs", [])
        }
    else:
        raise HTTPException(status_code=404, detail=f"User with username {username} not found")


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
        "track_id": data.track_id,
        "track_name": data.track_name,
        "track_artist": data.track_artist,
        "track_album": data.track_album,
        "track_release_year": data.track_release_year,
        "track_rating": data.track_rating,
        "like_list": []
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


@app.post("/tracks/get_track_details", summary="Get Details", response_model=Track)
async def get_details(track_id: int):
    track = await app.mongodb.tracks.find_one({"track_id": track_id})
    if track:
        return track
    else:
        return {"message": f"Track with ID {track_id} does not exist."}


@app.post("/tracks/like_track", summary="Like a track as a user")
async def like_track(username: str, track_id: int):

    data_track = await app.mongodb.tracks.find_one({"track_id": track_id})
    data_user = await app.mongodb.users.find_one({"username": username})

    if not data_track:
        raise HTTPException(status_code=404, detail=f"Track with ID {track_id} not found")

    elif not data_user:
        raise HTTPException(status_code=404, detail=f"User with {username} username not found")

    new_liked_songs = data_user["liked_songs"]
    new_liked_songs.append(track_id)

    await app.mongodb.users.find_one_and_update(
        {"username": username},
        {"$set":
            {
                "liked_songs": new_liked_songs
            }
        },
        return_document=ReturnDocument.AFTER
    )

    new_like_list = data_track["like_list"]
    new_like_list.append(username)

    await app.mongodb.tracks.find_one_and_update(
        {"track_id": track_id},
        {"$set":
            {
                "like_list": new_like_list
            }
        },
        return_document=ReturnDocument.AFTER
    )

    return {"message": f"Track {track_id} liked."}


@app.post("/tracks/unlike_track", summary="Unlike a track as a user")
async def unlike_track(username: str, track_id: int):

    data_track = await app.mongodb.tracks.find_one({"track_id": track_id})
    data_user = await app.mongodb.users.find_one({"username": username})

    if not data_track:
        raise HTTPException(status_code=404, detail=f"Track with ID {track_id} not found")

    elif not data_user:
        raise HTTPException(status_code=404, detail=f"User with {username} username not found")

    new_unliked_songs = data_user["unliked_songs"]
    new_unliked_songs.append(track_id)

    await app.mongodb.users.find_one_and_update(
        {"username": username},
        {"$set":
            {
                "unliked_songs": new_unliked_songs
            }
        },
        return_document=ReturnDocument.AFTER
    )

    new_unlike_list = data_track["unlike_list"]
    new_unlike_list.append(username)

    await app.mongodb.tracks.find_one_and_update(
        {"track_id": track_id},
        {"$set":
            {
                "unlike_list": new_unlike_list
            }
        },
        return_document=ReturnDocument.AFTER
    )

    return {"message": f"Track {track_id} unliked."}


@app.post("/tracks/get_like_unlike", summary="Get number of likes per track")
async def like_track(track_id: int):
    data_track = await app.mongodb.tracks.find_one({"track_id": track_id})

    if not data_track:
        raise HTTPException(status_code=404, detail=f"Track with ID {track_id} not found")

    like_num = len(data_track["like_list"])
    unlike_num = len(data_track["like_list"])

    return {
        "like_num": like_num,
        "unlike_num": unlike_num,
        "message": f"number of likes & unlikes for track {track_id}"
    }
