from bson import ObjectId
from fastapi import HTTPException

from app.models.repositories.playlists_repo import PlaylistsRepo
from app.models.repositories.users_repo import UsersRepo
from app.models.repositories.prompts_repo import PromptsRepo
from app.services.playlist_generation_service import PlaylistGenerationService
from app.services.spotify_playlist_service import SpotifyPlaylistService


class PlaylistsController:
    def __init__(self):
        self.playlists_repo = PlaylistsRepo()
        self.users_repo = UsersRepo()
        self.prompts_repo = PromptsRepo()
        self.generator = PlaylistGenerationService()
        self.spotify_playlist_service = SpotifyPlaylistService()

    async def generate_only(self, *, user_id: str, prompt: str, min_songs: int, max_songs: int):
        songs = await self.generator.generate(prompt, min_songs=min_songs, max_songs=max_songs)

        await self.prompts_repo.create_generation_log(
            user_id=user_id,
            prompt=prompt,
            min_songs=min_songs,
            max_songs=max_songs,
            response_songs=songs,
        )

        return {
            "name_suggestion": "AI Playlist",
            "description_suggestion": None,
            "source_prompt": prompt,
            "songs": songs,
            "total_songs": len(songs),
        }

    async def save_playlist(
        self,
        *,
        user_id: str,
        name: str,
        description: str | None,
        songs,
        source_prompt: str | None,
        total_songs: int | None,
        total_duration_ms: int | None,
    ):
        final_total = total_songs if total_songs is not None else len(songs)

        doc = await self.playlists_repo.create(
            user_id=ObjectId(user_id),
            name=name,
            description=description,
            songs=[s if isinstance(s, dict) else s.model_dump() for s in songs],
            source_prompt=source_prompt,
            total_songs=final_total,
            total_duration_ms=total_duration_ms,
        )
        return doc

    async def get(self, playlist_id: str):
        return await self.playlists_repo.get(playlist_id)

    async def list_by_user(self, user_id: str, limit: int = 50, skip: int = 0):
        return await self.playlists_repo.list_by_user(user_id, limit=limit, skip=skip)

    async def update(self, *, playlist_id: str, payload):
        updates = {}
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.description is not None:
            updates["description"] = payload.description
        if payload.songs is not None:
            updates["songs"] = [s if isinstance(s, dict) else s.model_dump() for s in payload.songs]
            updates["total_songs"] = len(updates["songs"])
        if payload.total_songs is not None:
            updates["total_songs"] = payload.total_songs
        if payload.total_duration_ms is not None:
            updates["total_duration_ms"] = payload.total_duration_ms

        return await self.playlists_repo.update(playlist_id, updates)

    async def delete(self, playlist_id: str):
        return await self.playlists_repo.delete(playlist_id)

    async def export_to_spotify(self, *, user_id: str, playlist_id: str, public: bool = False):
        playlist_doc = await self.playlists_repo.get(playlist_id)
        if not playlist_doc:
            raise HTTPException(status_code=404, detail="Playlist not found")

        if str(playlist_doc["user_id"]) != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        user_doc = await self.users_repo.get(user_id)
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        return await self.spotify_playlist_service.export_playlist(
            user_doc=user_doc,
            playlist_doc=playlist_doc,
            public=public,
        )
