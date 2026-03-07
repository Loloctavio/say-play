import base64
import os
import re
import time
import unicodedata
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import ConnectionError, ReadTimeout


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _normalize(s: str) -> str:
    if not s:
        return ""
    s = s.lower().strip()
    s = _strip_accents(s)
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"\[.*?\]", " ", s)
    s = re.sub(r"\bfeat\.?\b|\bft\.?\b", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _token_overlap_score(a: str, b: str) -> float:
    ta = set(_normalize(a).split())
    tb = set(_normalize(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _score_match(input_track: str, input_artist: str, cand_track: str, cand_artist: str) -> float:
    name_score = _token_overlap_score(input_track, cand_track)
    artist_score = _token_overlap_score(input_artist, cand_artist) if input_artist else 0.0
    return 0.75 * name_score + 0.25 * artist_score


class SpotifyVerifier:
    """
    Verify tracks with Spotify using Client Credentials.
    Requires:
      - SPOTIFY_CLIENT_ID
      - SPOTIFY_CLIENT_SECRET
    """

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, timeout: int = 60):
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET", "")
        if not self.client_id or not self.client_secret:
            raise ValueError("Missing SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET in env.")
        self.timeout = timeout
        self._token: Optional[str] = None

    def _get_token(self) -> str:
        if self._token:
            return self._token

        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {auth}"},
            data={"grant_type": "client_credentials"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        self._token = response.json()["access_token"]
        return self._token

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def _search(self, track: str, artist: str | None = None, limit: int = 5) -> list[dict]:
        q = f'track:"{track}"'
        if artist:
            q += f' artist:"{artist}"'

        for attempt in range(1, 5):
            try:
                response = requests.get(
                    "https://api.spotify.com/v1/search",
                    headers=self._headers(),
                    params={"q": q, "type": "track", "limit": str(limit)},
                    timeout=self.timeout,
                )

                # Refresh token once if token expired/invalid.
                if response.status_code == 401 and attempt == 1:
                    self._token = None
                    continue

                # Respect Spotify rate-limits.
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait_s = float(retry_after) if retry_after and retry_after.isdigit() else 0.8 * (2 ** (attempt - 1))
                    time.sleep(max(0.5, min(wait_s, 10.0)))
                    continue

                if response.status_code >= 500:
                    time.sleep(0.8 * (2 ** (attempt - 1)))
                    continue

                response.raise_for_status()
                return response.json().get("tracks", {}).get("items", [])
            except (ReadTimeout, ConnectionError):
                time.sleep(0.8 * (2 ** (attempt - 1)))

        return []

    def verify_track(self, track: str, artist: str) -> Dict[str, Any]:
        items = self._search(track, artist, limit=5)

        if not items and artist:
            items = self._search(track, None, limit=5)

        if not items:
            return {"status": "not_found", "confidence": 0.0}

        best_sc, best = 0.0, items[0]
        for item in items:
            item_name = item.get("name", "")
            item_artist = (item.get("artists") or [{}])[0].get("name", "")
            score = _score_match(track, artist, item_name, item_artist)
            if score > best_sc:
                best_sc, best = score, item

        confidence = float(best_sc)
        status = "verified" if confidence >= 0.72 else "maybe"

        return {
            "status": status,
            "confidence": round(confidence, 3),
            "spotify_id": best.get("id"),
            "spotify_url": (best.get("external_urls") or {}).get("spotify"),
            "matched_track": best.get("name"),
            "matched_artist": (best.get("artists") or [{}])[0].get("name"),
            "preview_url": best.get("preview_url"),
        }

    def verify_list(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for track in tracks:
            try:
                verified = self.verify_track(track=track["track"], artist=track["artist"])
            except Exception as exc:
                verified = {"status": "error", "confidence": 0.0, "error": str(exc)}

            enriched = dict(track)
            enriched["verified"] = verified
            out.append(enriched)

        return out
