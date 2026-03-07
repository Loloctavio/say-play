import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.mongo import close_mongo, ensure_indexes, ping
from app.routes.playlists_routes import router as playlists_router
from app.routes.spotify_routes import router as spotify_router
from app.routes.user_routes import router as users_router

app = FastAPI(title="AI Playlist API", version="0.1.0")

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
extra_origins = [x.strip() for x in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if x.strip()]
allow_origins = [frontend_url, *extra_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(users_router)
app.include_router(playlists_router)
app.include_router(spotify_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
async def _startup():
    await ping()
    await ensure_indexes()


@app.on_event("shutdown")
def _shutdown():
    close_mongo()
