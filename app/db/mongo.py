from __future__ import annotations

import os
from typing import Dict
from dotenv import load_dotenv
import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "ai-playlist")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set in .env")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_db() -> AsyncIOMotorDatabase:
    global _client, _db
    if _db is not None:
        return _db

    _client = AsyncIOMotorClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        appname="ai-playlist",
    )

    _db = _client[MONGO_DB]
    return _db


def get_collection(name: str):
    return get_db()[name]


def get_collections() -> Dict[str, object]:
    db = get_db()
    return {
        "users": db["users"],
        "playlists": db["playlists"],
        "prompts": db["prompts"],
    }


async def ping() -> bool:
    await get_db().command("ping")
    return True


def close_mongo() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
