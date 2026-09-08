"""
Routing and OSRM integration package for QITRO.
"""

from backend.core.routing.osrm_client import (
    fetch_osrm_distance_matrix,
    fetch_osrm_route_geometry,
    batch_fetch_route_geometries,
)

__all__ = [
    "fetch_osrm_distance_matrix",
    "fetch_osrm_route_geometry",
    "batch_fetch_route_geometries",
]
