from fastapi import APIRouter, Depends, HTTPException, Query
from app.controllers.playlists_controller import PlaylistsController
from app.models.playlist_schemas import (
    PlaylistGenerateRequest,
    PlaylistDraftOut,
    PlaylistSaveRequest,
    PlaylistUpdate,
    PlaylistOut,
    SpotifyExportOut,
    SpotifyExportRequest,
)
from app.services.dependencies import get_current_user

router = APIRouter(prefix="/playlists", tags=["playlists"])
controller = PlaylistsController()


def _serialize_playlist(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": str(doc["user_id"]),
        "name": doc.get("name"),
        "description": doc.get("description"),
        "source_prompt": doc.get("source_prompt"),
        "songs": doc.get("songs", []),
        "total_songs": doc.get("total_songs", len(doc.get("songs", []))),
        "total_duration_ms": doc.get("total_duration_ms"),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


@router.post("/generate", response_model=PlaylistDraftOut)
async def generate_playlist(
    payload: PlaylistGenerateRequest,
    current_user=Depends(get_current_user),
):
    draft = await controller.generate_only(
        user_id=current_user["id"],
        prompt=payload.prompt,
        min_songs=payload.min_songs,
        max_songs=payload.max_songs,
    )
    return draft


@router.post("", response_model=PlaylistOut)
async def save_playlist(
    payload: PlaylistSaveRequest,
    current_user=Depends(get_current_user),
):
    doc = await controller.save_playlist(
        user_id=current_user["id"],
        name=payload.name,
        description=payload.description,
        songs=payload.songs,
        source_prompt=payload.source_prompt,
        total_songs=payload.total_songs,
        total_duration_ms=payload.total_duration_ms,
    )
    return _serialize_playlist(doc)


@router.get("", response_model=list[PlaylistOut])
async def list_my_playlists(
    current_user=Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
):
    docs = await controller.list_by_user(current_user["id"], limit=limit, skip=skip)
    return [_serialize_playlist(d) for d in docs]


@router.get("/{playlist_id}", response_model=PlaylistOut)
async def get_playlist(
    playlist_id: str,
    current_user=Depends(get_current_user),
):
    doc = await controller.get(playlist_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")

    if str(doc["user_id"]) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    return _serialize_playlist(doc)


@router.put("/{playlist_id}", response_model=PlaylistOut)
async def update_playlist(
    playlist_id: str,
    payload: PlaylistUpdate,
    current_user=Depends(get_current_user),
):
    doc = await controller.get(playlist_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if str(doc["user_id"]) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    updated = await controller.update(playlist_id=playlist_id, payload=payload)
    return _serialize_playlist(updated)


@router.post("/{playlist_id}/spotify", response_model=SpotifyExportOut)
async def export_playlist_to_spotify(
    playlist_id: str,
    payload: SpotifyExportRequest,
    current_user=Depends(get_current_user),
):
    return await controller.export_to_spotify(
        user_id=current_user["id"],
        playlist_id=playlist_id,
        public=payload.public,
    )


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: str,
    current_user=Depends(get_current_user),
):
    doc = await controller.get(playlist_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if str(doc["user_id"]) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    ok = await controller.delete(playlist_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Playlist not found")

    return {"deleted": True}
