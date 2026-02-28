from typing import Any, Optional, Type
from agents.base import BaseMusicAgentBuilder, AgentDefaults
#from agents.tools.spotify_tool import spotify_verify

class MusicAgentFactory:
    def __init__(
        self,
        *,
        model: Any,
        output_schema: Optional[Type[Any]] = None,
        defaults: AgentDefaults = AgentDefaults(),
        shared_tools: Optional[list[Any]] = None,
    ):
        self.builder = BaseMusicAgentBuilder(
            model=model,
            defaults=defaults,
            #shared_tools=[spotify_verify],
            output_schema=output_schema,
            tools=shared_tools,
        )

    def discovery(self):
        return self.builder.build(
            name="Discovery",
            role="Discover new music similar to the user’s taste with controlled novelty.",
            extra_instructions="""
            - If the user gives an artist/track: produce similar + adjacent recommendations.
            - Include variety across 2–4 micro-genres.
            """,
        )
    
    def genre(self):
        return self.builder.build(
            name="Genre",
            role="Recommend based on a target genre or micro-genres related to the user prompt.",
            extra_instructions="""
            - If no genre is specified, infer 2–4 relevant micro-genres from the prompt.
            - Spread across substyles to avoid repetition.
            """,
        )

    def rhythm(self):
        return self.builder.build(
            name="Rhythm",
            role="Recommend based on rhythm/tempo/groove (steady, upbeat, downtempo, syncopated).",
            extra_instructions="""
            - If missing, assume a tempo range based on the user activity (study=mid/low).
            - Keep songs consistent in groove so it’s easy to stay focused.
            """,
        )

    def language(self):
        return self.builder.build(
            name="Language",
            role="Recommend based on language constraints (Spanish/English/etc.) and vocal density.",
            extra_instructions="""
            - Ask only if language is important; otherwise infer from prompt.
            - Offer a balanced mix (e.g., 70/30) if user is open to bilingual.
            """,
        )

    def popularity(self):
        return self.builder.build(
            name="Popularity",
            role="Recommend with a popularity strategy: mainstream vs deep cuts vs rising artists.",
            extra_instructions="""
            - Create a popularity mix unless user specifies: e.g., 40% known, 40% mid, 20% obscure.
            - Avoid repeating the same artists too much.
            """,
        )

    def mood(self):
        return self.builder.build(
            name="Mood",
            role="Match music to mood/activity (study, gym, drive, focus).",
            extra_instructions="""
            - If missing context, ask only: mood + energy (1-10) + vocals yes/no.
            """,
        )

    def playlist(self):
        return self.builder.build(
            name="Playlist",
            role="Build playlists with pacing and transitions.",
            extra_instructions="""
            - Always propose an arc: warm-up → core → cooldown.
            """,
        )