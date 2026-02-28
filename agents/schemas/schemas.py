from pydantic import BaseModel, Field
from typing import List, Optional

class TrackRec(BaseModel):
    artist: str
    track: str
    reason: str
    genres: Optional[List[str]] = None

class MusicRecs(BaseModel):
    summary: str
    quick_picks: List[TrackRec] = Field(default_factory=list)
    deeper_cuts: List[TrackRec] = Field(default_factory=list)
    next_question: str

class TrackWithSource(BaseModel):
    artist: str
    track: str
    reason: str
    genres: Optional[List[str]] = None
    suggested_by: List[str] = Field(default_factory=list)

class TeamRecommendationResponse(BaseModel):
    summary: str
    tracks: List[TrackWithSource] = Field(default_factory=list)
    next_question: str