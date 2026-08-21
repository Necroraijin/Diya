"""
OpenStreetMap ingestion via the Overpass API.

Overpass is rate-limited and occasionally slow, and PRD §8.1 is explicit that we
must not hit it live during a demo. So: fetch once, cache the raw response to
disk, and serve from cache forever after. `?refresh=true` forces a re-fetch.

If Overpass is unreachable and no cache exists, callers fall back to the bundled
demo geometry — a demo must never fail on someone else's uptime.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

import httpx

OVERPASS_URL = os.environ.get("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
CACHE_DIR = Path(os.environ.get("OSM_CACHE_DIR", "/app/osm-cache"))
CACHE_TTL_SECONDS = int(os.environ.get("OSM_CACHE_TTL", 60 * 60 * 24 * 30))


def cache_path(city: str) -> Path:
    return CACHE_DIR / f"{city}.json"


def read_cache(city: str) -> Optional[dict[str, Any]]:
    path = cache_path(city)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if time.time() - payload.get("_fetched_at", 0) > CACHE_TTL_SECONDS:
        return None
    return payload


def write_cache(city: str, payload: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {**payload, "_fetched_at": time.time()}
    cache_path(city).write_text(json.dumps(payload), encoding="utf-8")


async def fetch_overpass(query: str, timeout: float = 60.0) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(OVERPASS_URL, data={"data": query})
        response.raise_for_status()
        return response.json()


def parse_overpass(raw: dict[str, Any]) -> dict[str, list[dict]]:
    """
    Turn a raw Overpass response into addressable mesh objects.

    Every way keeps its OSM id as a stable handle (PRD §8.2) so agents can emit
    `wayId: 48213001` in a mesh_edit record instead of raw geometry.
    """
    nodes = {
        element["id"]: (element["lon"], element["lat"])
        for element in raw.get("elements", [])
        if element.get("type") == "node"
    }

    buildings: list[dict] = []
    roads: list[dict] = []

    for element in raw.get("elements", []):
        if element.get("type") != "way":
            continue
        tags = element.get("tags", {})
        coords = [nodes[n] for n in element.get("nodes", []) if n in nodes]
        if len(coords) < 2:
            continue

        way_id = f"way-{element['id']}"

        if "building" in tags:
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            buildings.append({
                "wayId": way_id,
                "coordinates": coords,
                "height": _building_height(tags),
                "name": tags.get("name"),
            })
        elif "highway" in tags:
            roads.append({
                "wayId": way_id,
                "path": coords,
                "name": tags.get("name", tags["highway"].replace("_", " ").title()),
                "width": _road_width(tags),
                "highway": tags["highway"],
            })

    return {"buildings": buildings, "roads": roads}


def _building_height(tags: dict) -> float:
    """Prefer an explicit height tag, then levels * 3.2m, then a default."""
    raw_height = tags.get("height") or tags.get("building:height")
    if raw_height:
        try:
            return float(str(raw_height).replace("m", "").strip())
        except ValueError:
            pass
    levels = tags.get("building:levels")
    if levels:
        try:
            return float(levels) * 3.2
        except ValueError:
            pass
    return 12.0


_ROAD_WIDTH_BY_CLASS = {
    "motorway": 6, "trunk": 5, "primary": 4,
    "secondary": 3, "tertiary": 3, "residential": 2,
}


def _road_width(tags: dict) -> int:
    return _ROAD_WIDTH_BY_CLASS.get(tags.get("highway", ""), 2)
