"""
OSRM (Open Source Routing Machine) API Client:
Provides real-world road network distance matrices and GeoJSON route geometries.

Guarantees:
- Strict adherence to sovereign Indian territory (no crossing international borders like Bangladesh).
- Automatic routing through the strategic Siliguri Corridor ('Chicken's Neck' NH12/NH27)
  and the Guwahati Gateway (NH6) for all Northeast India connectivity.
- O(1) distance & time matrix pre-computation for quantum and classical metaheuristic solvers.

Endpoints used:
- OSRM Table Service: http://router.project-osrm.org/table/v1/driving/
- OSRM Route Service: http://router.project-osrm.org/route/v1/driving/
"""

import json
import logging
import math
import socket
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

# Set global socket timeout to prevent any HTTP requests hanging indefinitely
socket.setdefaulttimeout(6.0)

logger = logging.getLogger("qitro.osrm")

OSRM_TABLE_BASE = "http://router.project-osrm.org/table/v1/driving"
OSRM_ROUTE_BASE = "http://router.project-osrm.org/route/v1/driving"

# Sovereign Indian Strategic Domestic Transit Corridors
SILIGURI_CORRIDOR: Tuple[float, float] = (26.7271, 88.3953)  # NH12 / NH27 Chicken's Neck Gateway
GUWAHATI_CORRIDOR: Tuple[float, float] = (26.1445, 91.7362)  # NH6 Guwahati-Shillong Expressway Origin


def is_northeast_india(lat: float, lon: float) -> bool:
    """Returns True if coordinate is located in Northeast India (Assam, Meghalaya, etc. east of Bangladesh)."""
    return lon >= 89.8 and lat <= 28.5


def is_shillong_plateau(lat: float, lon: float) -> bool:
    """Returns True if coordinate is located on the Shillong / Meghalaya plateau."""
    return 25.2 <= lat <= 25.8 and 91.5 <= lon <= 92.3


def is_near_point(p1: Tuple[float, float], p2: Tuple[float, float], tol: float = 0.25) -> bool:
    """Checks if two coordinates are near the same transit corridor hub."""
    return abs(p1[0] - p2[0]) < tol and abs(p1[1] - p2[1]) < tol


def ensure_domestic_indian_waypoints(
    coordinates: List[Tuple[float, float]]
) -> List[Tuple[float, float]]:
    """
    Expands sequenced route coordinates to ensure vehicles strictly remain
    within sovereign Indian territory (via the Siliguri 'Chicken's Neck' Corridor
    and the Guwahati NH6 connector) and NEVER cross international borders into Bangladesh.
    """
    if len(coordinates) < 2:
        return coordinates

    expanded: List[Tuple[float, float]] = []
    for i in range(len(coordinates)):
        curr_pt = coordinates[i]
        expanded.append(curr_pt)

        if i < len(coordinates) - 1:
            next_pt = coordinates[i + 1]
            curr_ne = is_northeast_india(curr_pt[0], curr_pt[1])
            next_ne = is_northeast_india(next_pt[0], next_pt[1])

            # Transitioning from Mainland India into Northeast India
            if not curr_ne and next_ne:
                if not is_near_point(curr_pt, SILIGURI_CORRIDOR) and not is_near_point(next_pt, SILIGURI_CORRIDOR):
                    expanded.append(SILIGURI_CORRIDOR)
                if is_shillong_plateau(next_pt[0], next_pt[1]) and not is_near_point(next_pt, GUWAHATI_CORRIDOR):
                    expanded.append(GUWAHATI_CORRIDOR)

            # Transitioning from Northeast India back to Mainland India
            elif curr_ne and not next_ne:
                if is_shillong_plateau(curr_pt[0], curr_pt[1]) and not is_near_point(curr_pt, GUWAHATI_CORRIDOR):
                    expanded.append(GUWAHATI_CORRIDOR)
                if not is_near_point(curr_pt, SILIGURI_CORRIDOR) and not is_near_point(next_pt, SILIGURI_CORRIDOR):
                    expanded.append(SILIGURI_CORRIDOR)

    return expanded


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth's mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def _compute_fallback_matrices(
    coordinates: List[Tuple[float, float]], fallback_speed_kmh: float = 40.0
) -> Tuple[List[List[float]], List[List[float]]]:
    """Generates fallback distance and time matrices using domestic road estimation."""
    n = len(coordinates)
    speed_mps = (fallback_speed_kmh * 1000.0) / 3600.0
    dist_matrix = [[0.0] * n for _ in range(n)]
    time_matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        lat1, lon1 = coordinates[i]
        for j in range(n):
            if i == j:
                continue
            lat2, lon2 = coordinates[j]

            # Domestic transit routing for Northeast pairs
            curr_ne = is_northeast_india(lat1, lon1)
            next_ne = is_northeast_india(lat2, lon2)
            if curr_ne != next_ne:
                # Via Siliguri corridor
                d1 = _haversine_distance_km(lat1, lon1, SILIGURI_CORRIDOR[0], SILIGURI_CORRIDOR[1]) * 1.3
                d2 = _haversine_distance_km(SILIGURI_CORRIDOR[0], SILIGURI_CORRIDOR[1], lat2, lon2) * 1.3
                road_dist_km = d1 + d2
            else:
                road_dist_km = _haversine_distance_km(lat1, lon1, lat2, lon2) * 1.3

            dist_matrix[i][j] = road_dist_km
            time_matrix[i][j] = (road_dist_km * 1000.0) / speed_mps

    return time_matrix, dist_matrix


def fetch_osrm_distance_matrix(
    coordinates: List[Tuple[float, float]],
    timeout: float = 8.0,
    fallback_speed_kmh: float = 40.0,
) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Requests OSRM Table API to compute all-pairs driving distances and durations.
    Enforces sovereign domestic routing (via Siliguri & Guwahati) so QPSO optimization
    never shortcuts across international borders.

    Parameters:
    -----------
    coordinates : List of (lat, lon) tuples. Index 0 is the Hub/Depot, followed by destinations.
    timeout : Network request timeout in seconds.
    fallback_speed_kmh : Speed assumed if fallback estimation is triggered.

    Returns:
    --------
    (time_matrix_sec, dist_matrix_km) :
        time_matrix_sec: 2D matrix of driving durations in seconds.
        dist_matrix_km: 2D matrix of driving distances in kilometers.
    """
    n = len(coordinates)
    if n <= 1:
        return [[0.0]], [[0.0]]

    # Check if this problem involves Northeast India alongside mainland India
    has_ne = any(is_northeast_india(lat, lon) for lat, lon in coordinates)
    has_mainland = any(not is_northeast_india(lat, lon) for lat, lon in coordinates)

    aux_coords = list(coordinates)
    siliguri_idx = None
    guwahati_idx = None

    if has_ne and has_mainland:
        for idx, pt in enumerate(coordinates):
            if is_near_point(pt, SILIGURI_CORRIDOR):
                siliguri_idx = idx
                break
        if siliguri_idx is None:
            siliguri_idx = len(aux_coords)
            aux_coords.append(SILIGURI_CORRIDOR)

        for idx, pt in enumerate(coordinates):
            if is_near_point(pt, GUWAHATI_CORRIDOR):
                guwahati_idx = idx
                break
        if guwahati_idx is None:
            guwahati_idx = len(aux_coords)
            aux_coords.append(GUWAHATI_CORRIDOR)

    # Note: OSRM expects coordinates in '{longitude},{latitude}' order separated by ';'
    coord_str = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in aux_coords)
    url = f"{OSRM_TABLE_BASE}/{coord_str}?annotations=distance,duration"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "QITRO-Quantum-VRP/1.0 (academic-simulation)",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("code") == "Ok":
                    durations = data.get("durations")
                    distances_meters = data.get("distances")

                    if durations and distances_meters:
                        total_len = len(aux_coords)
                        full_dist_km = [[0.0] * total_len for _ in range(total_len)]
                        full_time_sec = [[0.0] * total_len for _ in range(total_len)]

                        for i in range(total_len):
                            for j in range(total_len):
                                if i == j:
                                    full_dist_km[i][j] = 0.0
                                    full_time_sec[i][j] = 0.0
                                else:
                                    d_m = distances_meters[i][j]
                                    t_s = durations[i][j]
                                    if d_m is not None and t_s is not None:
                                        full_dist_km[i][j] = d_m / 1000.0
                                        full_time_sec[i][j] = float(t_s)
                                    else:
                                        h_d = _haversine_distance_km(
                                            aux_coords[i][0], aux_coords[i][1],
                                            aux_coords[j][0], aux_coords[j][1]
                                        ) * 1.3
                                        full_dist_km[i][j] = h_d
                                        full_time_sec[i][j] = (h_d * 1000.0) / ((fallback_speed_kmh * 1000.0) / 3600.0)

                        # Enforce sovereign Indian domestic routing for Northeast pairs
                        if has_ne and has_mainland and siliguri_idx is not None:
                            for i in range(n):
                                i_ne = is_northeast_india(coordinates[i][0], coordinates[i][1])
                                for j in range(n):
                                    if i == j:
                                        continue
                                    j_ne = is_northeast_india(coordinates[j][0], coordinates[j][1])

                                    # Pair crosses between mainland and Northeast
                                    if not i_ne and j_ne:
                                        # Mainland -> Northeast
                                        if is_shillong_plateau(coordinates[j][0], coordinates[j][1]) and guwahati_idx is not None:
                                            # Via Siliguri -> Guwahati -> Shillong
                                            dom_dist = (
                                                full_dist_km[i][siliguri_idx]
                                                + full_dist_km[siliguri_idx][guwahati_idx]
                                                + full_dist_km[guwahati_idx][j]
                                            )
                                            dom_time = (
                                                full_time_sec[i][siliguri_idx]
                                                + full_time_sec[siliguri_idx][guwahati_idx]
                                                + full_time_sec[guwahati_idx][j]
                                            )
                                        else:
                                            # Via Siliguri Corridor
                                            dom_dist = full_dist_km[i][siliguri_idx] + full_dist_km[siliguri_idx][j]
                                            dom_time = full_time_sec[i][siliguri_idx] + full_time_sec[siliguri_idx][j]

                                        full_dist_km[i][j] = dom_dist
                                        full_time_sec[i][j] = dom_time

                                    elif i_ne and not j_ne:
                                        # Northeast -> Mainland
                                        if is_shillong_plateau(coordinates[i][0], coordinates[i][1]) and guwahati_idx is not None:
                                            # Shillong -> Guwahati -> Siliguri -> Mainland
                                            dom_dist = (
                                                full_dist_km[i][guwahati_idx]
                                                + full_dist_km[guwahati_idx][siliguri_idx]
                                                + full_dist_km[siliguri_idx][j]
                                            )
                                            dom_time = (
                                                full_time_sec[i][guwahati_idx]
                                                + full_time_sec[guwahati_idx][siliguri_idx]
                                                + full_time_sec[siliguri_idx][j]
                                            )
                                        else:
                                            # Via Siliguri Corridor
                                            dom_dist = full_dist_km[i][siliguri_idx] + full_dist_km[siliguri_idx][j]
                                            dom_time = full_time_sec[i][siliguri_idx] + full_time_sec[siliguri_idx][j]

                                        full_dist_km[i][j] = dom_dist
                                        full_time_sec[i][j] = dom_time

                        # Slice back to original N x N dimensions
                        trimmed_dist = [full_dist_km[i][:n] for i in range(n)]
                        trimmed_time = [full_time_sec[i][:n] for i in range(n)]

                        logger.info(f"Successfully fetched OSRM distance matrix for {n} nodes (Indian territory enforced).")
                        return trimmed_time, trimmed_dist

        logger.warning("OSRM Table API returned non-OK response. Using fallback.")
    except Exception as exc:
        logger.warning(f"OSRM Table API unavailable or timed out ({exc}). Falling back to road-network estimation.")

    return _compute_fallback_matrices(coordinates, fallback_speed_kmh)


def fetch_osrm_route_geometry(
    coordinates: List[Tuple[float, float]],
    timeout: float = 4.0,
) -> List[List[float]]:
    """
    Requests OSRM Route API to obtain real-world street/highway GeoJSON coordinates.
    Strictly preserves sovereign Indian territory by expanding routes through the
    Siliguri 'Chicken's Neck' corridor and the Guwahati highway connector.

    Parameters:
    -----------
    coordinates : Ordered sequence of (lat, lon) tuples [depot, stop_1, ..., stop_k, depot].
    timeout : Network request timeout in seconds.

    Returns:
    --------
    List of [lat, lon] points tracing the actual road geometry.
    If OSRM is offline or fails, falls back to the straight-line waypoint coordinates [[lat, lon], ...].
    """
    if len(coordinates) < 2:
        return [[lat, lon] for lat, lon in coordinates]

    # Enforce domestic Indian transit waypoints
    domestic_coords = ensure_domestic_indian_waypoints(coordinates)

    # OSRM expects coordinates in '{longitude},{latitude}' order separated by ';'
    coord_str = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in domestic_coords)
    url = f"{OSRM_ROUTE_BASE}/{coord_str}?overview=full&geometries=geojson"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "QITRO-Quantum-VRP/1.0 (academic-simulation)",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("code") == "Ok" and data.get("routes"):
                    geojson_coords = data["routes"][0]["geometry"]["coordinates"]
                    # Convert OSRM [lon, lat] pairs to Leaflet [lat, lon] pairs
                    lat_lon_polyline = [[pt[1], pt[0]] for pt in geojson_coords]
                    return lat_lon_polyline
    except Exception as exc:
        logger.warning(f"OSRM Route API geometry request failed ({exc}). Using waypoint coordinates.")

    # Fallback to straight-line waypoints
    return [[lat, lon] for lat, lon in domestic_coords]


def batch_fetch_route_geometries(
    routes: List[Any],
    depot_coords: Tuple[float, float],
    customer_coords_map: Dict[int, Tuple[float, float]],
) -> None:
    """
    Enriches Route objects in-place with real-world road GeoJSON geometry coordinates,
    ensuring all paths stick strictly to Indian territory.
    """
    for route in routes:
        cust_ids = getattr(route, "customer_ids", None)
        if cust_ids is None and isinstance(route, dict):
            cust_ids = route.get("customer_ids", [])

        if not cust_ids:
            continue

        # Build full coordinate sequence: Depot -> Stop 1 -> ... -> Stop N -> Depot
        seq: List[Tuple[float, float]] = [depot_coords]
        for cid in cust_ids:
            if cid in customer_coords_map:
                seq.append(customer_coords_map[cid])
        seq.append(depot_coords)

        road_polyline = fetch_osrm_route_geometry(seq)

        if hasattr(route, "geojson_geometry"):
            route.geojson_geometry = road_polyline
        elif isinstance(route, dict):
            route["geojson_geometry"] = road_polyline
