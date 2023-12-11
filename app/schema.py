from pydantic import BaseModel, EmailStr


class User(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserDetail(User):
    friends: list
    liked_songs: list
    liked_songs_date: list


class Track(BaseModel):
    track_id: str
    track_name: str
    track_artist: list
    track_album: str
    track_release_year: int
    # track_rating: dict
    like_list: list


class AddTrack(BaseModel):
    track_name: str
    track_artist: list
    track_album: str
    genre: str
    track_release_year: int


"""
class Artist(BaseModel):
    artist_name: str
    artist_albums: list
    artist_tracks: list
    artist_id: str
    artist_rating: int


class Album(BaseModel):
    album_name: str
    album_tracks: list
    album_performers: list
    album_id: str
    album_release_year: int
"""