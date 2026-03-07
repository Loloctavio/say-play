from datetime import datetime

from bson import ObjectId

from app.db.mongo import get_collections

cols = get_collections()
playlists_col = cols["playlists"]


class PlaylistsRepo:
    async def create(
        self,
        user_id: ObjectId,
        name: str,
        description: str | None,
        songs: list[dict],
        source_prompt: str | None,
        total_songs: int,
        total_duration_ms: int | None,
    ):
        now = datetime.utcnow()
        doc = {
            "user_id": user_id,
            "name": name,
            "description": description,
            "source_prompt": source_prompt,
            "songs": songs,
            "total_songs": total_songs,
            "total_duration_ms": total_duration_ms,
            "created_at": now,
            "updated_at": now,
        }
        res = await playlists_col.insert_one(doc)
        doc["_id"] = res.inserted_id
        return doc

    async def get(self, playlist_id: str):
        return await playlists_col.find_one({"_id": ObjectId(playlist_id)})

    async def list_by_user(self, user_id: str, limit: int = 50, skip: int = 0):
        cursor = playlists_col.find({"user_id": ObjectId(user_id)}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def update(self, playlist_id: str, updates: dict):
        updates["updated_at"] = datetime.utcnow()
        await playlists_col.update_one({"_id": ObjectId(playlist_id)}, {"$set": updates})
        return await self.get(playlist_id)

    async def delete(self, playlist_id: str):
        res = await playlists_col.delete_one({"_id": ObjectId(playlist_id)})
        return res.deleted_count > 0

    async def delete_by_user(self, user_id: str) -> int:
        res = await playlists_col.delete_many({"user_id": ObjectId(user_id)})
        return int(res.deleted_count)
