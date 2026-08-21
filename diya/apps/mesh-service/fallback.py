"""
Bundled demo geometry.

Used only when Overpass is unreachable and no disk cache exists. Deliberately
small and hand-digitised over the real target wards (PRD red flag #3 recommends
exactly this fallback), covering the road segments the seeded conflicts sit on.
"""

CITIES = {
    "mumbai": {
        "name": "Mumbai",
        "ward": "K/W — Andheri West",
        "center": [72.8464, 19.1197],
        "zoom": 15,
        # Overpass bbox is (south, west, north, east).
        "bbox": (19.115, 72.840, 19.125, 72.852),
    },
    "delhi": {
        "name": "Delhi",
        "ward": "Chandni Chowk",
        "center": [77.2310, 28.6562],
        "zoom": 15,
        "bbox": (28.650, 77.225, 28.660, 77.235),
    },
}


def overpass_query(bbox: tuple[float, float, float, float]) -> str:
    south, west, north, east = bbox
    area = f"{south},{west},{north},{east}"
    return (
        "[out:json][timeout:60];"
        f'(way["building"]({area});way["highway"]({area}););'
        "out body;>;out skel qt;"
    )


def _rect(min_lng, min_lat, w, h, height, way_id, name=None):
    return {
        "wayId": way_id,
        "name": name,
        "height": height,
        "coordinates": [
            [min_lng, min_lat],
            [min_lng + w, min_lat],
            [min_lng + w, min_lat + h],
            [min_lng, min_lat + h],
            [min_lng, min_lat],
        ],
    }


MUMBAI = {
    "buildings": [
        _rect(72.8450, 19.1190, 0.0010, 0.0010, 30, "bld-mum-001"),
        _rect(72.8462, 19.1188, 0.0010, 0.0010, 45, "bld-mum-002"),
        _rect(72.8440, 19.1195, 0.0008, 0.0010, 20, "bld-mum-003"),
        _rect(72.8474, 19.1192, 0.0010, 0.0010, 55, "bld-mum-004"),
        _rect(72.8445, 19.1178, 0.0010, 0.0010, 35, "bld-mum-005"),
        _rect(72.8458, 19.1204, 0.0009, 0.0008, 26, "bld-mum-006"),
        _rect(72.8478, 19.1178, 0.0011, 0.0009, 41, "bld-mum-007"),
        _rect(72.8432, 19.1186, 0.0008, 0.0011, 18, "bld-mum-008"),
        _rect(72.8466, 19.1210, 0.0010, 0.0009, 33, "bld-mum-009"),
        _rect(72.8486, 19.1196, 0.0009, 0.0010, 48, "bld-mum-010"),
    ],
    "roads": [
        {
            "wayId": "way-48213001", "name": "SV Road", "width": 4, "highway": "primary",
            "path": [[72.8430, 19.1197], [72.8445, 19.1197], [72.8460, 19.1197],
                     [72.8475, 19.1197], [72.8490, 19.1197]],
        },
        {
            "wayId": "way-48213010", "name": "DN Nagar Road", "width": 3, "highway": "secondary",
            "path": [[72.8450, 19.1170], [72.8450, 19.1185], [72.8450, 19.1200],
                     [72.8450, 19.1215]],
        },
        {
            "wayId": "way-48213011", "name": "Link Road", "width": 3, "highway": "secondary",
            "path": [[72.8470, 19.1170], [72.8470, 19.1185], [72.8470, 19.1200],
                     [72.8470, 19.1215]],
        },
        {
            "wayId": "way-48213012", "name": "Veera Desai Road", "width": 2, "highway": "tertiary",
            "path": [[72.8435, 19.1210], [72.8455, 19.1208], [72.8478, 19.1206]],
        },
        {
            "wayId": "way-48213013", "name": "Andheri Subway Approach", "width": 2, "highway": "residential",
            "path": [[72.8455, 19.1180], [72.8462, 19.1188], [72.8464, 19.1197]],
        },
    ],
}

DELHI = {
    "buildings": [
        _rect(77.2300, 28.6555, 0.0010, 0.0010, 15, "bld-del-001"),
        _rect(77.2312, 28.6558, 0.0010, 0.0010, 12, "bld-del-002"),
        _rect(77.2290, 28.6566, 0.0009, 0.0008, 18, "bld-del-003"),
        _rect(77.2324, 28.6552, 0.0011, 0.0009, 14, "bld-del-004"),
        _rect(77.2304, 28.6570, 0.0010, 0.0008, 21, "bld-del-005"),
    ],
    "roads": [
        {
            "wayId": "way-92001001", "name": "Chandni Chowk Road", "width": 4, "highway": "primary",
            "path": [[77.2280, 28.6562], [77.2295, 28.6562], [77.2310, 28.6562],
                     [77.2325, 28.6562], [77.2340, 28.6562]],
        },
        {
            "wayId": "way-92001002", "name": "Nai Sarak", "width": 2, "highway": "residential",
            "path": [[77.2308, 28.6548], [77.2308, 28.6562], [77.2308, 28.6574]],
        },
    ],
}

GEOMETRY = {"mumbai": MUMBAI, "delhi": DELHI}
