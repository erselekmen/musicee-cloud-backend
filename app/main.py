import random
import requests
from fastapi.exception_handlers import HTTPException
import secrets
import base64
import json
import logging
from fastapi import status, File, UploadFile
from datetime import datetime, timedelta
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

API_URL = "http://musicee.us-west-2.elasticbeanstalk.com"


@app.get("/api/health")
def root():
    return {"message": "Welcome to Musicee API"}


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

    if username == friend_username:
        raise HTTPException(status_code=404, detail="You cannot add yourself friend")

    user = await get_user_by_username(username)
    friend = await get_user_by_username(friend_username)

    if user and friend:
        if friend_username not in user.get("friends", []):
            user_friends = user.get("friends", [])
            user_friends.append(friend_username)

            user_friends2 = friend.get("friends", [])
            user_friends2.append(username)

            await update_user_details(username, user_friends)
            await update_user_details(friend_username, user_friends2)
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
            "liked_songs": user.get("liked_songs", []),
            "liked_songs_date": user.get("liked_songs_date",[]),
        }

    else:
        raise HTTPException(status_code=404, detail=f"User with username {username} not found")


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
async def add_track(data: AddTrack):
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please check track information!"
        )

    random_bytes = secrets.token_bytes(6)

    track_id = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')

    track = {
        "track_id": track_id,
        "track_name": data.track_name,
        "track_artist": data.track_artist,
        "track_album": data.track_album,
        "genre": data.genre,
        "track_release_year": data.track_release_year,
        # "track_rating": {},
        "like_list": [],
    }

    await app.mongodb.tracks.insert_one(track)

    return {
        "message": "Track added successfully.",
        "track_id": track_id
    }


@app.put("/tracks/update_track/{track_id}", summary="Update track")
async def update_track(data: AddTrack, track_id: str):
    await app.mongodb.tracks.find_one_and_update(
        {"track_id": track_id},
        {"$set":
            {
                "track_name": data.track_name,
                "track_artist": data.track_artist,
                "track_album": data.track_album,
                "genre": data.genre,
                "track_release_year": data.track_release_year
            }
        },
        return_document=ReturnDocument.AFTER
    )

    return {"message": f"Track with ID {track_id} has been updated."}


@app.delete("/tracks/delete_track/{track_id}", summary="Delete track")
async def delete_track(track_id: str):

    track = await app.mongodb.tracks.find_one({"track_id": track_id})

    if track is None:
        raise HTTPException(status_code=404, detail=f"message: Track with ID {track_id} does not exist.")

    await app.mongodb.tracks.delete_one({"track_id": track_id})

    users = app.mongodb.users.find({})

    if users is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No users were found!"
        )

    async for user in users:

        if track_id not in user["liked_songs"]:
            continue

        user["liked_songs"].remove(track_id)
        user["liked_songs_date"] = [
            song for song in user["liked_songs_date"] if track_id not in song
        ]
        await app.mongodb.users.find_one_and_update(
            {"username": user["username"]},
            {
                "$set":
                    {
                        "liked_songs": user["liked_songs"],
                        "liked_songs_date": user["liked_songs_date"]
                    }
            },
            return_document=ReturnDocument.AFTER
        )

    return {"message": f"Track with ID {track_id} has been deleted."}


@app.post("/tracks/get_track_name/{track_id}", summary="Get track name by ID", response_model=str)
async def get_track_name(track_id: str):
    track = await app.mongodb.tracks.find_one({"track_id": track_id}, {"track_name": 1})

    if track and "track_name" in track:
        return track["track_name"]
    else:
        raise HTTPException(status_code=404, detail=f"Track with ID {track_id} not found")


@app.post("/tracks/get_track_details", summary="Get Details", response_model=Track)
async def get_details(track_id: str):
    track = await app.mongodb.tracks.find_one({"track_id": track_id})
    if track:
        return track
    else:
        raise HTTPException(status_code=404, detail=f"message: Track with ID {track_id} does not exist.")


@app.post("/tracks/like_track", summary="Like a track as a user")
async def like_track(username: str, track_id: str):

    data_track = await app.mongodb.tracks.find_one({"track_id": track_id})
    data_user = await app.mongodb.users.find_one({"username": username})

    if not data_track and not data_user:
        raise HTTPException(status_code=404, detail=f"Track ID {track_id} or User {username} not found")

    if track_id in data_user["liked_songs"]:

        data_user["liked_songs"].remove(track_id)
        data_user["liked_songs_date"] = [
            song for song in data_user["liked_songs_date"] if track_id not in song
        ]
        await app.mongodb.users.find_one_and_update(
            {"username": username},
            {
                "$set":
                    {
                        "liked_songs": data_user["liked_songs"],
                        "liked_songs_date": data_user["liked_songs_date"]
                    }
            },
            return_document=ReturnDocument.AFTER
        )

        data_track["like_list"].remove(username)

        await app.mongodb.tracks.find_one_and_update(
            {"track_id": track_id},
            {
                "$set":
                    {
                        "like_list": data_track["like_list"]
                    }
            },
            return_document=ReturnDocument.AFTER
        )

        return {"message": f"Track {track_id} unliked."}

    new_liked_songs = data_user["liked_songs"]
    new_liked_songs.append(track_id)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    liked_songs_date = data_user.get("liked_songs_date", [])
    liked_songs_date.append({track_id: current_time})

    await app.mongodb.users.find_one_and_update(
        {"username": username},
        {"$set":
            {
                "liked_songs": new_liked_songs,
                "liked_songs_date": liked_songs_date
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



@app.get("/users/liked_songs_past_6_months/{username}", summary="Get songs liked in the past 6 months")
async def get_liked_songs_past_6_months(username: str):

    user = await app.mongodb.users.find_one({"username": username})

    if not user:
        raise HTTPException(status_code=404, detail=f"User with username {username} not found")

    liked_songs_date = user.get("liked_songs_date", [])

    six_months_ago = datetime.now() - timedelta(days=180)

    songs_past_6_months = [
        track_id for item in liked_songs_date
        for track_id, liked_time in item.items()
        if datetime.strptime(liked_time, "%Y-%m-%d %H:%M:%S") >= six_months_ago
    ]

    return {"username": username, "liked_songs_past_6_months": songs_past_6_months}


@app.post("/tracks/get_like", summary="Get number of likes per track")
async def like_track(track_id: str):
    data_track = await app.mongodb.tracks.find_one({"track_id": track_id})

    if not data_track:
        raise HTTPException(status_code=404, detail=f"Track with ID {track_id} not found")

    like_num = len(data_track["like_list"])
    # unlike_num = len(data_track["unlike_list"])

    return {
        "like_num": like_num,
        # "unlike_num": unlike_num,
        "message": f"number of like for track {track_id}"
    }


@app.post("/tracks/upload_track_file/")
async def create_upload_file(file: UploadFile = File()):

    try:
        content = await file.read()

        content_json = json.loads(content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    track_json = []

    for each in content_json:

        random_bytes = secrets.token_bytes(6)
        track_id = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')

        track = {
            "track_id": track_id,
            "track_name": each["track_name"],
            "track_artist": each["track_artist"],
            "track_album": each["track_album"],
            "genre": each["genre"],
            "track_release_year": each["track_release_year"],
            "like_list": []
        }
        track_json.append(track)

    try:
        await app.mongodb.tracks.insert_many(track_json)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    return {"message": "Track file imported successfully."}


@app.post("/tracks/recommend_track")
async def recommend_track(username: str):

    user_data = await app.mongodb.users.find_one({"username": username})

    if user_data is None:
        raise HTTPException(status_code=500, detail=f"User {username} not found")

    recommend_list = []
    same_genre = []
    for track in user_data["liked_songs"]:

        track_response = await app.mongodb.tracks.find_one({"track_id": track})

        if track_response is None:
            raise HTTPException(status_code=500, detail="No such song found")

        track_genre = track_response["genre"]

        cursor = app.mongodb.tracks.find({"genre": track_genre})
        count = await app.mongodb.tracks.count_documents({"genre": track_genre})

        async for document in cursor:
            if document["track_id"] != track:
                same_genre.append(document["track_id"])
            else:
                continue

        if count == 0:
            continue
        elif 1 <= count <= 2:
            ran_list = random.choices(same_genre, None, k=count)
            recommend_list += ran_list
        else:
            ran_list = random.choices(same_genre, None, k=3)
            recommend_list += ran_list

    recommend_list_new = list(set(recommend_list))
    return recommend_list_new

@app.post("/tracks/recommend_friend_track")
async def recommend_friend_track(username: str):

    user_data = await app.mongodb.users.find_one({"username": username})

    if user_data is None:
        raise HTTPException(status_code=500, detail=f"User {username} not found")

    friend_list = user_data["friends"]

    if not friend_list:
        raise HTTPException(status_code=500, detail=f"User {username} has no friend")

    my_friend_songs = []

    for value in range(len(friend_list)):

        friend_username = friend_list[value]

        try:
            friend_response = requests.get(f"{API_URL}/users/get_user_details/{friend_username}")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

        friend_response = json.loads(friend_response.content.decode('utf-8'))

        friend_liked_songs = friend_response["liked_songs"]

        if len(friend_liked_songs) == 0:
            continue

        elif len(friend_liked_songs) == 1:
            my_friend_songs.append(friend_liked_songs[0])
            continue

        dummy_my_friend_songs = random.choices(friend_liked_songs, None, k=5)

        set_my_friend_songs = set(dummy_my_friend_songs) | set(my_friend_songs)
        my_friend_songs = list(set_my_friend_songs)

    return my_friend_songs


@app.post("/tracks/recommend_artist_track", operation_id="recommend_artist_track")
async def recommend_artist_track(username: str):
    # Step 1: Retrieve user data
    user_data = await app.mongodb.users.find_one({"username": username})

    if user_data is None:
        raise HTTPException(status_code=404, detail=f"User {username} not found")

    recommend_list = []

    for liked_song_id in user_data.get("liked_songs", []):

        track_response = await app.mongodb.tracks.find_one({"track_id": liked_song_id})

        if track_response is None:
            logging.warning(f"No information found for song {liked_song_id}")
            continue

        track_artist = track_response.get("track_artist")

        cursor = app.mongodb.tracks.find({"track_artist": track_artist, "track_id": {"$ne": liked_song_id}})
        same_artist_tracks = await cursor.to_list(length=None)

        if len(same_artist_tracks) > 0:
            count = min(len(same_artist_tracks), 3)
            ran_list = random.sample(same_artist_tracks, count)
            recommend_list.extend(track["track_name"] for track in ran_list)

    return recommend_list
