from datetime import datetime
from bson import ObjectId
from app.db.mongo import get_collections

cols = get_collections()
users_col = cols["users"]


class UsersRepo:
    async def create(self, *, username: str, gmail: str, hashed_password: str, profile_photo: str | None):
        now = datetime.utcnow()
        existing = await users_col.find_one({"gmail": gmail})
        if existing:
            return None, "Gmail already exists"

        doc = {
            "username": username,
            "gmail": gmail,
            "password": hashed_password,
            "profile_photo": profile_photo,
            "playlists": [],
            "spotify_connected": False,
            "created_at": now,
            "updated_at": now,
        }
        res = await users_col.insert_one(doc)
        doc["_id"] = res.inserted_id
        return doc, None

    async def get(self, user_id: str):
        return await users_col.find_one({"_id": ObjectId(user_id)})

    async def find_by_gmail(self, gmail: str):
        return await users_col.find_one({"gmail": gmail})

    async def find_by_spotify_oauth_state(self, state: str):
        return await users_col.find_one({"spotify_oauth_state": state})

    async def update(self, user_id: str, updates: dict):
        updates["updated_at"] = datetime.utcnow()
        await users_col.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
        return await self.get(user_id)

    async def delete(self, user_id: str) -> bool:
        res = await users_col.delete_one({"_id": ObjectId(user_id)})
        return res.deleted_count > 0

    async def add_playlist(self, user_id: str, playlist_id: str):
        await users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"playlists": ObjectId(playlist_id)}, "$set": {"updated_at": datetime.utcnow()}},
        )

    async def remove_playlist(self, user_id: str, playlist_id: str):
        await users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"playlists": ObjectId(playlist_id)}, "$set": {"updated_at": datetime.utcnow()}},
        )
