from app.db.mongo import db
from app.services.auth_service import hash_password, verify_password, create_access_token
from fastapi import HTTPException
from datetime import datetime
from bson import ObjectId

users_collection = db["users"]

async def register_user(data):
    existing = await users_collection.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = {
        "email": data.email,
        "password": hash_password(data.password),
        "created_at": datetime.utcnow()
    }

    result = await users_collection.insert_one(user)
    token = create_access_token({"sub": data.email})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

async def login_user(data):
    user = await users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user["email"]})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

async def get_user_by_email(email: str):
    user = await users_collection.find_one({"email": email})
    if not user:
        return None

    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "created_at": user["created_at"]
    }