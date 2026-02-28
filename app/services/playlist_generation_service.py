import asyncio
from typing import List, Dict, Any

from agno.models.openai import OpenAIResponses
from agents.factory import MusicAgentFactory
from agents.async_team import AsyncCollaborativeMusicTeam
from agents.team import merge_agent_recs, select_final_list
from agents.spotify_verifier import SpotifyVerifier
from agents.schemas.schemas import MusicRecs

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

    async def generate(self, prompt: str, min_songs: int = 35, max_songs: int = 50) -> List[Dict[str, Any]]:
        agents = self.build_agents()
        team = AsyncCollaborativeMusicTeam(agents)

        outputs = await team.run_all(prompt)
        merged = merge_agent_recs(outputs)
        final_list = select_final_list(merged, min_n=min_songs, max_n=max_songs)

        verifier = SpotifyVerifier()
        verified_list = await asyncio.to_thread(verifier.verify_list, final_list)

        return verified_list