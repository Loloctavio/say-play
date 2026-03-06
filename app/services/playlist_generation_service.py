import asyncio
import re
from typing import List, Dict, Any

from agno.models.openai import OpenAIResponses
from agents.factory import MusicAgentFactory
from agents.async_team import AsyncCollaborativeMusicTeam
from agents.team import merge_agent_recs, select_final_list
from agents.spotify_verifier import SpotifyVerifier
from agents.schemas.schemas import MusicRecs


def _extract_requested_song_count(prompt: str) -> int | None:
    text = (prompt or "").lower()

    patterns = [
        r"\b(?:exactly|just|only|around|about)?\s*(\d{1,3})\s*(?:songs?|tracks?|canciones?)\b",
        r"\btop\s*(\d{1,3})\b",
        r"\b(\d{1,3})\s*(?:song|track|cancion|canciones)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue

        try:
            value = int(match.group(1))
        except (TypeError, ValueError):
            continue

        if 1 <= value <= 200:
            return value

    return None


class PlaylistGenerationService:
    def build_agents(self):
        model = OpenAIResponses(id="gpt-5.2")
        factory = MusicAgentFactory(model=model, output_schema=MusicRecs)
        return {
            "discovery": factory.discovery(),
            "mood": factory.mood(),
            "playlist": factory.playlist(),
            "genre": factory.genre(),
            "rhythm": factory.rhythm(),
            "language": factory.language(),
            "popularity": factory.popularity(),
        }

    async def generate(self, prompt: str, min_songs: int = 15, max_songs: int = 25) -> List[Dict[str, Any]]:
        requested = _extract_requested_song_count(prompt)

        if requested is not None:
            min_songs = requested
            max_songs = requested
        elif min_songs > max_songs:
            min_songs, max_songs = max_songs, min_songs

        agents = self.build_agents()
        team = AsyncCollaborativeMusicTeam(agents)

        outputs = await team.run_all(prompt)
        merged = merge_agent_recs(outputs)
        final_list = select_final_list(merged, min_n=min_songs, max_n=max_songs)

        verifier = SpotifyVerifier()
        verified_list = await asyncio.to_thread(verifier.verify_list, final_list)

        return verified_list
