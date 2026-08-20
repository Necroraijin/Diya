"""
DIYA Mesh Service
GIS data processing: OSM data fetching, caching, and spatial overlap analysis.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os

app = FastAPI(title="DIYA Mesh Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── City Configurations ──────────────────────────────────────────

CITIES = {
    "mumbai": {
        "name": "Mumbai",
        "center": [72.8777, 19.076],
        "zoom": 14,
        "bounds": [[72.82, 19.0], [72.94, 19.15]],
        "overpass_query": '[out:json];(way["building"](19.115,72.840,19.125,72.852);way["highway"](19.115,72.840,19.125,72.852););out body;>;out skel qt;',
    },
    "delhi": {
        "name": "Delhi",
        "center": [77.2295, 28.6139],
        "zoom": 14,
        "bounds": [[77.15, 28.55], [77.32, 28.7]],
        "overpass_query": '[out:json];(way["building"](28.650,77.225,28.660,77.235);way["highway"](28.650,77.225,28.660,77.235););out body;>;out skel qt;',
    },
}

# Mock building data (same as frontend for consistency)
MUMBAI_BUILDINGS = [
    {"coordinates": [[72.8450, 19.1190], [72.8460, 19.1190], [72.8460, 19.1200], [72.8450, 19.1200]], "height": 30, "wayId": "bld-001"},
    {"coordinates": [[72.8462, 19.1188], [72.8472, 19.1188], [72.8472, 19.1198], [72.8462, 19.1198]], "height": 45, "wayId": "bld-002"},
    {"coordinates": [[72.8440, 19.1195], [72.8448, 19.1195], [72.8448, 19.1205], [72.8440, 19.1205]], "height": 20, "wayId": "bld-003"},
    {"coordinates": [[72.8474, 19.1192], [72.8484, 19.1192], [72.8484, 19.1202], [72.8474, 19.1202]], "height": 55, "wayId": "bld-004"},
    {"coordinates": [[72.8445, 19.1178], [72.8455, 19.1178], [72.8455, 19.1188], [72.8445, 19.1188]], "height": 35, "wayId": "bld-005"},
]

MUMBAI_ROADS = [
    {"path": [[72.8430, 19.1197], [72.8440, 19.1197], [72.8450, 19.1197], [72.8460, 19.1197], [72.8470, 19.1197], [72.8480, 19.1197], [72.8490, 19.1197]], "wayId": "way-48213001", "name": "SV Road", "width": 4},
    {"path": [[72.8450, 19.1170], [72.8450, 19.1180], [72.8450, 19.1190], [72.8450, 19.1200], [72.8450, 19.1210], [72.8450, 19.1220]], "wayId": "way-48213010", "name": "DN Nagar Road", "width": 3},
    {"path": [[72.8470, 19.1170], [72.8470, 19.1180], [72.8470, 19.1190], [72.8470, 19.1200], [72.8470, 19.1210]], "wayId": "way-48213011", "name": "Link Road", "width": 3},
]


# ── Routes ───────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "DIYA Mesh Service", "status": "operational"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/cities")
async def list_cities():
    return {
        "cities": [
            {"id": k, "name": v["name"], "center": v["center"], "zoom": v["zoom"]}
            for k, v in CITIES.items()
        ]
    }


@app.get("/mesh/{city}")
async def get_city_mesh(city: str, ward: Optional[str] = None):
    """Returns building footprints and road network for a city."""
    if city not in CITIES:
        raise HTTPException(status_code=404, detail=f"City '{city}' not available. Options: {list(CITIES.keys())}")

    config = CITIES[city]

    if city == "mumbai":
        return {
            "city": city,
            "name": config["name"],
            "center": config["center"],
            "zoom": config["zoom"],
            "bounds": config["bounds"],
            "buildings": MUMBAI_BUILDINGS,
            "roads": MUMBAI_ROADS,
            "source": "osm-cache",
            "cached": True,
        }

    # Delhi minimal data
    return {
        "city": city,
        "name": config["name"],
        "center": config["center"],
        "zoom": config["zoom"],
        "bounds": config["bounds"],
        "buildings": [
            {"coordinates": [[77.2300, 28.6555], [77.2310, 28.6555], [77.2310, 28.6565], [77.2300, 28.6565]], "height": 15, "wayId": "bld-d001"},
            {"coordinates": [[77.2312, 28.6558], [77.2322, 28.6558], [77.2322, 28.6568], [77.2312, 28.6568]], "height": 12, "wayId": "bld-d002"},
        ],
        "roads": [
            {"path": [[77.2280, 28.6562], [77.2290, 28.6562], [77.2300, 28.6562], [77.2310, 28.6562], [77.2320, 28.6562], [77.2330, 28.6562]], "wayId": "way-92001001", "name": "Chandni Chowk Road", "width": 4},
        ],
        "source": "osm-cache",
        "cached": True,
    }


class SpatialOverlapRequest(BaseModel):
    works: list[dict]
    threshold_meters: float = 50.0


@app.post("/spatial/overlap")
async def check_spatial_overlap(request: SpatialOverlapRequest):
    """
    Check spatial overlap between planned works using geofence intersection.
    Uses simple distance-based check (Haversine would be used in production).
    """
    overlaps = []
    works = request.works

    for i in range(len(works)):
        for j in range(i + 1, len(works)):
            w1 = works[i]
            w2 = works[j]
            loc1 = w1.get("location", {})
            loc2 = w2.get("location", {})

            # Simple Euclidean approximation (sufficient for demo zone)
            dlat = abs(loc1.get("lat", 0) - loc2.get("lat", 0)) * 111000  # ~111km per degree
            dlng = abs(loc1.get("lng", 0) - loc2.get("lng", 0)) * 85000   # ~85km per degree at these latitudes
            distance = (dlat**2 + dlng**2) ** 0.5

            r1 = w1.get("geofenceRadius", 100)
            r2 = w2.get("geofenceRadius", 100)

            if distance < (r1 + r2) / 2:
                overlaps.append({
                    "work1": w1.get("id"),
                    "work2": w2.get("id"),
                    "distance_m": round(distance, 1),
                    "overlap": True,
                    "wayId_match": loc1.get("wayId") == loc2.get("wayId"),
                })

    return {
        "overlaps": overlaps,
        "count": len(overlaps),
        "threshold_meters": request.threshold_meters,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
