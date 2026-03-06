from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.playlists_routes import router as playlists_router
from app.routes.spotify_routes import router as spotify_router
from app.routes.user_routes import router as users_router
from app.db.mongo import ping, close_mongo

app = FastAPI(title="AI Playlist API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.on_event("shutdown")
def _shutdown():
    close_mongo()
