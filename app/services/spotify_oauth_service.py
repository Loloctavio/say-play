from __future__ import annotations

import base64
import os
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import aiohttp
from fastapi import HTTPException, status

from app.services.spotify_http import spotify_request_json

SPOTIFY_ACCOUNTS_BASE = "https://accounts.spotify.com"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"


class SpotifyOAuthService:
    def __init__(self) -> None:
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")
        self.scopes = os.getenv("SPOTIFY_SCOPES")

        if not self.client_id or not self.client_secret or not self.redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Missing Spotify OAuth env vars",
            )

    @staticmethod
    def generate_state() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def state_expires_at(minutes: int = 10) -> datetime:
        return datetime.utcnow() + timedelta(minutes=minutes)

    def build_authorize_url(self, *, state: str) -> str:
        query = urlencode(
            {
                "client_id": self.client_id,
                "response_type": "code",
                "redirect_uri": self.redirect_uri,
                "scope": self.scopes,
                "state": state,
                "show_dialog": "false",
            }
        )
        return f"{SPOTIFY_ACCOUNTS_BASE}/authorize?{query}"

    async def exchange_code(self, *, code: str) -> dict:
        credentials = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        basic = base64.b64encode(credentials).decode("utf-8")

        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        async with aiohttp.ClientSession() as session:
            return await spotify_request_json(
                session,
                method="POST",
                url=f"{SPOTIFY_ACCOUNTS_BASE}/api/token",
                headers=headers,
                data=body,
                timeout=20,
                context="Spotify token exchange",
            )

    async def get_profile(self, *, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with aiohttp.ClientSession() as session:
            return await spotify_request_json(
                session,
                method="GET",
                url=f"{SPOTIFY_API_BASE}/me",
                headers=headers,
                timeout=20,
                context="Spotify profile fetch",
            )
