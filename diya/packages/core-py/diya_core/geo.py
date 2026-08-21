"""
Geospatial helpers.

Kept dependency-free (pure stdlib `math`) so that every service can import it.
The mesh-service layers shapely on top of this for polygon-level work; for
point+radius geofences the haversine distance below is exact enough and much
cheaper.
"""

from __future__ import annotations

import math

EARTH_RADIUS_M = 6_371_008.8


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres between two WGS84 points."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def geofences_intersect(
    lat1: float, lng1: float, r1: float,
    lat2: float, lng2: float, r2: float,
) -> tuple[bool, float, float]:
    """
    Two circular geofences intersect when the centre distance is less than the
    sum of their radii.

    Returns (intersects, centre_distance_m, overlap_depth_m) where overlap depth
    is how far the circles penetrate each other — used to rank conflict severity.
    """
    distance = haversine_m(lat1, lng1, lat2, lng2)
    overlap_depth = (r1 + r2) - distance
    return overlap_depth > 0, distance, max(0.0, overlap_depth)


def bbox_of(points: list[tuple[float, float]], pad_deg: float = 0.0) -> list[list[float]]:
    """Bounding box [[min_lng, min_lat], [max_lng, max_lat]] for (lng, lat) points."""
    lngs = [p[0] for p in points]
    lats = [p[1] for p in points]
    return [
        [min(lngs) - pad_deg, min(lats) - pad_deg],
        [max(lngs) + pad_deg, max(lats) + pad_deg],
    ]
