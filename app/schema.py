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
    favorite_songs: list
    liked_songs: list


class Track(BaseModel):
    track_id: int
    track_name: str
    track_artist: list
    track_album: str
    track_release_year: int
    track_rating: int
    like_list: list


class Artist(BaseModel):
    artist_name: str
    artist_albums: list
    artist_tracks: list
    artist_id: int
    artist_rating: int


class Album(BaseModel):
    album_name: str
    album_tracks: list
    album_performers: list
    album_id: int
    album_release_year: int
