from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class VerifiedMeta(BaseModel):
    status: str = "not_found"
    confidence: float = 0.0
    spotify_id: Optional[str] = None
    spotify_url: Optional[str] = None
    matched_track: Optional[str] = None
    matched_artist: Optional[str] = None
    preview_url: Optional[str] = None

class Song(BaseModel):
    artist: str = Field(min_length=1)
    track: str = Field(min_length=1)
    reason: Optional[str] = None
    genres: List[str] = []
    suggested_by: List[str] = []
    verified: Optional[VerifiedMeta] = None

class PlaylistGenerateRequest(BaseModel):
    prompt: str
    min_songs: int = Field(default=35, ge=1, le=200)
    max_songs: int = Field(default=50, ge=1, le=200)

class PlaylistDraftOut(BaseModel):
    name_suggestion: str = "AI Playlist"
    description_suggestion: Optional[str] = None
    source_prompt: str
    songs: List[Song]
    total_songs: int

class PlaylistSaveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=400)
    songs: List[Song] = Field(default_factory=list)
    total_songs: Optional[int] = Field(default=None, ge=0)
    total_duration_ms: Optional[int] = Field(default=None, ge=0)
    source_prompt: Optional[str] = None

class PlaylistUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=400)
    songs: Optional[List[Song]] = None
    total_songs: Optional[int] = Field(default=None, ge=0)
    total_duration_ms: Optional[int] = Field(default=None, ge=0)

class PlaylistOut(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    source_prompt: Optional[str] = None
    songs: List[Song]
    total_songs: int
    total_duration_ms: Optional[int] = None
    created_at: datetime
    updated_at: datetime