"""
DIYA Mesh Service

GIS subsystem (PRD §8): OSM ingestion with disk caching, addressable mesh
objects keyed by OSM way id, and shapely-backed spatial analysis of the
geofences attached to planned works.

Spatial maths runs in a local equirectangular projection centred on the city, so
shapely operates in metres rather than degrees and intersection areas are real
areas rather than meaningless degree-squared numbers.
"""

from __future__ import annotations

import math
import os
from typing import Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from shapely.geometry import LineString, Point, mapping
from shapely.ops import unary_union

import fallback
import osm

app = FastAPI(
    title="DIYA Mesh Service",
    description="OSM ingestion and spatial conflict analysis",
    version="2.0.0",
)

ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Local projection ─────────────────────────────────────────────

class LocalProjection:
    """
    Equirectangular projection about a city centre.

    Accurate to well under a metre across a 1–2 km² demo zone, which is all
    PRD §3 scopes us to, and avoids pulling pyproj into the image.
    """

    METRES_PER_DEGREE_LAT = 111_320.0

    def __init__(self, center_lng: float, center_lat: float) -> None:
        self.center_lng = center_lng
        self.center_lat = center_lat
        self.metres_per_degree_lng = self.METRES_PER_DEGREE_LAT * math.cos(
            math.radians(center_lat)
        )

    def to_m(self, lng: float, lat: float) -> tuple[float, float]:
        return (
            (lng - self.center_lng) * self.metres_per_degree_lng,
            (lat - self.center_lat) * self.METRES_PER_DEGREE_LAT,
        )

    def to_deg(self, x: float, y: float) -> tuple[float, float]:
        return (
            self.center_lng + x / self.metres_per_degree_lng,
            self.center_lat + y / self.METRES_PER_DEGREE_LAT,
        )


def _projection_for(works: list[dict]) -> LocalProjection:
    lats = [w["location"]["lat"] for w in works]
    lngs = [w["location"]["lng"] for w in works]
    return LocalProjection(sum(lngs) / len(lngs), sum(lats) / len(lats))


def _geofence(work: dict, projection: LocalProjection):
    loc = work["location"]
    x, y = projection.to_m(loc["lng"], loc["lat"])
    radius = work.get("geofenceRadius") or work.get("geofence_radius_m") or 100
    # quad_segs=32 keeps the circle smooth enough that area error is < 0.1%.
    return Point(x, y).buffer(float(radius), quad_segs=32)


# ── Models ───────────────────────────────────────────────────────

class SpatialOverlapRequest(BaseModel):
    works: list[dict]
    min_overlap_area_m2: float = Field(
        default=0.0, description="Discard intersections smaller than this."
    )


class ConflictZoneRequest(BaseModel):
    works: list[dict]
    simplify_tolerance_m: float = 5.0


# ── Routes ───────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "DIYA Mesh Service", "status": "operational", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "overpass_url": osm.OVERPASS_URL,
        "cache_dir": str(osm.CACHE_DIR),
        "cached_cities": sorted(
            p.stem for p in osm.CACHE_DIR.glob("*.json")
        ) if osm.CACHE_DIR.is_dir() else [],
    }


@app.get("/cities")
async def list_cities():
    return {
        "cities": [
            {
                "id": key,
                "name": cfg["name"],
                "ward": cfg["ward"],
                "center": cfg["center"],
                "zoom": cfg["zoom"],
                "bbox": cfg["bbox"],
            }
            for key, cfg in fallback.CITIES.items()
        ]
    }


@app.get("/mesh/{city}")
async def get_city_mesh(
    city: str,
    refresh: bool = Query(False, description="Bypass cache and re-query Overpass"),
):
    """
    Building footprints and road network for a city.

    Resolution order: disk cache -> Overpass -> bundled fallback geometry.
    """
    if city not in fallback.CITIES:
        raise HTTPException(
            status_code=404,
            detail=f"City '{city}' not available. Options: {sorted(fallback.CITIES)}",
        )

    config = fallback.CITIES[city]
    source = "fallback-bundled"
    geometry = fallback.GEOMETRY[city]

    cached = None if refresh else osm.read_cache(city)
    if cached:
        geometry = {"buildings": cached["buildings"], "roads": cached["roads"]}
        source = "osm-cache"
    else:
        try:
            raw = await osm.fetch_overpass(fallback.overpass_query(config["bbox"]))
            parsed = osm.parse_overpass(raw)
            if parsed["buildings"] or parsed["roads"]:
                osm.write_cache(city, parsed)
                geometry = parsed
                source = "osm-live"
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            # PRD red flag #3: OSM coverage/availability must never be a demo risk.
            print(f"[mesh] Overpass unavailable for {city} ({exc}); using bundled geometry.")

    return {
        "city": city,
        "name": config["name"],
        "ward": config["ward"],
        "center": config["center"],
        "zoom": config["zoom"],
        "bbox": config["bbox"],
        "buildings": geometry["buildings"],
        "roads": geometry["roads"],
        "counts": {
            "buildings": len(geometry["buildings"]),
            "roads": len(geometry["roads"]),
        },
        "source": source,
    }


@app.post("/spatial/overlap")
async def check_spatial_overlap(request: SpatialOverlapRequest):
    """
    Pairwise geofence intersection across the supplied works.

    Unlike a centroid-distance check this reports the actual intersecting area,
    which is what makes "how badly do these two collide" answerable.
    """
    works = request.works
    if len(works) < 2:
        return {"overlaps": [], "count": 0, "analysed_works": len(works)}

    projection = _projection_for(works)
    fences = {w["id"]: _geofence(w, projection) for w in works}
    overlaps: list[dict[str, Any]] = []

    for i in range(len(works)):
        for j in range(i + 1, len(works)):
            a, b = works[i], works[j]
            fa, fb = fences[a["id"]], fences[b["id"]]
            if not fa.intersects(fb):
                continue

            intersection = fa.intersection(fb)
            area = intersection.area
            if area < request.min_overlap_area_m2:
                continue

            ax, ay = projection.to_m(a["location"]["lng"], a["location"]["lat"])
            bx, by = projection.to_m(b["location"]["lng"], b["location"]["lat"])
            distance = math.hypot(ax - bx, ay - by)

            overlaps.append({
                "work1": a["id"],
                "work2": b["id"],
                "distance_m": round(distance, 1),
                "intersection_area_m2": round(area, 1),
                "overlap_fraction": round(area / min(fa.area, fb.area), 3),
                "same_way_id": a["location"].get("wayId") == b["location"].get("wayId"),
                "way_id": a["location"].get("wayId"),
            })

    overlaps.sort(key=lambda o: -o["intersection_area_m2"])
    return {
        "overlaps": overlaps,
        "count": len(overlaps),
        "analysed_works": len(works),
    }


@app.post("/spatial/conflict-zones")
async def conflict_zones(request: ConflictZoneRequest):
    """
    Dissolved GeoJSON polygons covering every area where two or more geofences
    intersect — the shape the map renders as a conflict overlay.
    """
    works = request.works
    if len(works) < 2:
        return {"type": "FeatureCollection", "features": []}

    projection = _projection_for(works)
    fences = [(w, _geofence(w, projection)) for w in works]

    pieces = []
    members: set[str] = set()
    for i in range(len(fences)):
        for j in range(i + 1, len(fences)):
            (wa, fa), (wb, fb) = fences[i], fences[j]
            if fa.intersects(fb):
                pieces.append(fa.intersection(fb))
                members.update({wa["id"], wb["id"]})

    if not pieces:
        return {"type": "FeatureCollection", "features": []}

    dissolved = unary_union(pieces).simplify(request.simplify_tolerance_m)
    polygons = list(getattr(dissolved, "geoms", [dissolved]))

    features = []
    for index, polygon in enumerate(polygons):
        geo = mapping(polygon)
        geo["coordinates"] = _coords_to_degrees(geo["coordinates"], projection)
        features.append({
            "type": "Feature",
            "id": f"zone-{index + 1}",
            "geometry": geo,
            "properties": {
                "area_m2": round(polygon.area, 1),
                "work_ids": sorted(members),
            },
        })

    return {"type": "FeatureCollection", "features": features}


@app.post("/spatial/works-on-way")
async def works_on_way(request: SpatialOverlapRequest, way_id: str = Query(...)):
    """Which works touch a given OSM way — the reverse lookup for map clicks."""
    matches = [
        w for w in request.works if w.get("location", {}).get("wayId") == way_id
    ]
    return {"way_id": way_id, "works": matches, "count": len(matches)}


def _coords_to_degrees(coords, projection: LocalProjection):
    """Recursively convert projected metre coordinates back to [lng, lat]."""
    if coords and isinstance(coords[0], (int, float)):
        return list(projection.to_deg(coords[0], coords[1]))
    return [_coords_to_degrees(c, projection) for c in coords]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
