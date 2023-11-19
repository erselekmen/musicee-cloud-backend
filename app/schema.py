from pydantic import BaseModel, EmailStr


class User(BaseModel):
    email: EmailStr
    password: str


class Track(BaseModel):
    track_name: str
    track_artist: list
    track_album: str
    track_rating: int
    track_id: int
    track_release_year: int


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
