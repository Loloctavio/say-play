from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException, status

from app.models.repositories.users_repo import UsersRepo
from app.services.spotify_oauth_service import SpotifyOAuthService


class SpotifyController:
    def __init__(self) -> None:
        self.repo = UsersRepo()
        self.oauth = SpotifyOAuthService()

    async def start_connect(self, *, user_id: str, redirect_to: str | None) -> dict:
        state = self.oauth.generate_state()
        state_expires_at = self.oauth.state_expires_at()

        await self.repo.update(
            user_id,
            {
                "spotify_oauth_state": state,
                "spotify_oauth_state_expires_at": state_expires_at,
                "spotify_oauth_redirect_to": redirect_to,
            },
        )

        return {
            "authorization_url": self.oauth.build_authorize_url(state=state),
            "state": state,
            "expires_at": state_expires_at,
        }

    async def handle_callback(self, *, code: str, state: str) -> dict:
        user = await self.repo.find_by_spotify_oauth_state(state)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

        expires_at = user.get("spotify_oauth_state_expires_at")
        if not expires_at or expires_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expired OAuth state")

        token_data = await self.oauth.exchange_code(code=code)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = int(token_data.get("expires_in", 3600))

        if not access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Spotify access_token")

        profile = await self.oauth.get_profile(access_token=access_token)
        spotify_user_id = profile.get("id")

        if not spotify_user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Spotify user id")

        now = datetime.utcnow()
        spotify_doc = {
            "spotify_user_id": spotify_user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": token_data.get("token_type", "Bearer"),
            "scope": token_data.get("scope"),
            "expires_at": now + timedelta(seconds=expires_in),
            "connected_at": now,
        }

        await self.repo.update(
            str(user["_id"]),
            {
                "spotify_connected": True,
                "spotify": spotify_doc,
                "spotify_oauth_state": None,
                "spotify_oauth_state_expires_at": None,
                "spotify_oauth_redirect_to": None,
            },
        )

        return {
            "connected": True,
            "user_id": str(user["_id"]),
            "spotify_user_id": spotify_user_id,
            "redirect_to": user.get("spotify_oauth_redirect_to"),
        }
