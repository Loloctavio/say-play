from __future__ import annotations
from typing import Dict, Tuple, List, Any
from collections import defaultdict

def _track_key(artist: str, track: str) -> Tuple[str, str]:
    return (artist.strip().lower(), track.strip().lower())

def merge_agent_recs(agent_outputs: Dict[str, Any]) -> List[dict]:
    """
    agent_outputs: { agent_key: MusicRecs }
    Returns merged list of dicts: {artist, track, reason, genres, suggested_by}
    """
    merged: dict[Tuple[str, str], dict] = {}
    sources = defaultdict(list)

    for agent_name, recs in agent_outputs.items():
        all_tracks = list(recs.quick_picks) + list(recs.deeper_cuts)

        for t in all_tracks:
            key = _track_key(t.artist, t.track)
            sources[key].append(agent_name)

            if key not in merged:
                merged[key] = {
                    "artist": t.artist,
                    "track": t.track,
                    "reason": t.reason,
                    "genres": t.genres or [],
                }
            else:
                if not merged[key]["genres"] and t.genres:
                    merged[key]["genres"] = t.genres

    result = []
    for key, data in merged.items():
        data["suggested_by"] = sorted(set(sources[key]))
        result.append(data)
    result.sort(key=lambda x: len(x["suggested_by"]), reverse=True)
    return result

def select_final_list(merged_tracks: List[dict], min_n: int = 35, max_n: int = 50) -> List[dict]:
    """
    Selecciona una lista final única (35–50):
    - Prioriza tracks con más consenso (ya vienen ordenadas).
    - Recorta a max_n.
    - Si por alguna razón hay menos de min_n, devuelve lo que exista.
    """
    final = merged_tracks[:max_n]
    if len(final) < min_n:
        return final
    return final