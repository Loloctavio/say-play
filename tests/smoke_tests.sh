#!/usr/bin/env bash
set -e

BASE="http://localhost:8000"

echo "1) Register..."
REGISTER_RES=$(curl -s -X POST "$BASE/users/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"octavio","gmail":"octavio@gmail.com","password":"12345678","profile_photo":null}' || true)

if echo "$REGISTER_RES" | grep -q "access_token"; then
  TOKEN=$(echo "$REGISTER_RES" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
else
  echo "User exists, logging in..."
  LOGIN_RES=$(curl -s -X POST "$BASE/users/login" \
    -H "Content-Type: application/json" \
    -d '{"gmail":"octavio@gmail.com","password":"12345678"}')
  TOKEN=$(echo "$LOGIN_RES" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
fi

echo "TOKEN OK"

echo "2) /users/me..."
curl -s "$BASE/users/me" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo "3) Generate playlist (no save)..."
DRAFT=$(curl -s -X POST "$BASE/playlists/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"indie rock for coding, not mainstream","min_songs":35,"max_songs":50}')

echo "$DRAFT" | python3 -m json.tool > /tmp/draft.json
echo "Draft saved to /tmp/draft.json"

SONGS=$(python3 - <<'PY'
import json
d=json.load(open("/tmp/draft.json"))
print(json.dumps(d["songs"]))
PY
)

echo "4) Save playlist..."
SAVED=$(curl -s -X POST "$BASE/playlists" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(python3 - <<PY
import json
songs = json.loads('''$SONGS''')
payload = {
  "name": "Coding Indie Rock",
  "description": "generated then saved",
  "source_prompt": "indie rock for coding, not mainstream",
  "songs": songs
}
print(json.dumps(payload))
PY
)")

echo "$SAVED" | python3 -m json.tool > /tmp/saved.json
PLAYLIST_ID=$(python3 - <<'PY'
import json
d=json.load(open("/tmp/saved.json"))
print(d["id"])
PY
)

echo "Saved playlist id: $PLAYLIST_ID"

echo "5) List playlists..."
curl -s "$BASE/playlists" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo "6) Get detail..."
curl -s "$BASE/playlists/$PLAYLIST_ID" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo "7) Update name..."
curl -s -X PUT "$BASE/playlists/$PLAYLIST_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Coding Indie Rock (v2)"}' | python3 -m json.tool

echo "8) Delete..."
curl -s -X DELETE "$BASE/playlists/$PLAYLIST_ID" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo "DONE ✅"