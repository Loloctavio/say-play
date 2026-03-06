from __future__ import annotations

from datetime import datetime

from bson import ObjectId

from app.db.mongo import get_collections

cols = get_collections()
prompts_col = cols["prompts"]


class PromptsRepo:
    async def create_generation_log(
        self,
        *,
        user_id: str,
        prompt: str,
        min_songs: int,
        max_songs: int,
        response_songs: list[dict],
    ) -> dict:
        now = datetime.utcnow()
        doc = {
            "user_id": ObjectId(user_id),
            "prompt": prompt,
            "request": {
                "min_songs": min_songs,
                "max_songs": max_songs,
            },
            "response": {
                "songs": response_songs,
                "total_songs": len(response_songs),
            },
            "created_at": now,
            "updated_at": now,
        }
        res = await prompts_col.insert_one(doc)
        doc["_id"] = res.inserted_id
        return doc
