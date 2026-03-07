from __future__ import annotations

import os
from typing import Dict

import certifi
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
PROMPTS_LOG_TTL_DAYS = max(1, int(os.getenv("PROMPTS_LOG_TTL_DAYS")))

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


async def ensure_indexes() -> None:
    db = get_db()

    # Best-effort index creation to avoid startup regressions in existing deployments.
    try:
        await db["users"].create_index("gmail")
        await db["users"].create_index("spotify_oauth_state")
        await db["playlists"].create_index([("user_id", 1), ("created_at", -1)])
        await db["prompts"].create_index([("user_id", 1), ("created_at", -1)])

        # TTL for generation logs so prompt+response history is not kept forever.
        await db["prompts"].create_index(
            "expires_at",
            expireAfterSeconds=0,
            name=f"prompts_ttl_{PROMPTS_LOG_TTL_DAYS}d",
        )
    except Exception:
        return


async def ping() -> bool:
    await get_db().command("ping")
    return True


def close_mongo() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
