from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    gmail: EmailStr
    password: str = Field(min_length=8)
    profile_photo: Optional[str] = None


class UserLogin(BaseModel):
    gmail: EmailStr
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=30)
    profile_photo: Optional[str] = None


class ChangePassword(BaseModel):
    old_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SpotifyInfoOut(BaseModel):
    spotify_user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    connected_at: Optional[datetime] = None


class UserOut(BaseModel):
    id: str
    username: str
    gmail: EmailStr
    profile_photo: Optional[str] = None
    playlists: List[str] = []
    spotify_connected: bool = False
    spotify: Optional[SpotifyInfoOut] = None
    created_at: datetime
    updated_at: datetime
