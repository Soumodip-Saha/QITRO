"""
Transportation Network Graph Model:
Handles multi-modal road networks, dynamic edge weights, Dijkstra/A* routing,
distance/time matrix computation, and realistic city map topologies.
"""

from dataclasses import dataclass, field
import heapq
import math
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import random

from backend.core.graph.traffic_models import (
    BPRCongestionModel,
    CMEMEmissionModel,
    RushHourProfile,
    TrafficIncident,
    WeatherCondition,
)


@dataclass
class Node:
    node_id: int
    lat: float
    lon: float
    name: str = ""
    is_depot: bool = False
    demand: float = 0.0
    time_window_start: float = 0.0  # seconds from t=0
    time_window_end: float = 86400.0  # seconds
    service_time: float = 300.0  # 5 min standard stop time


@dataclass
class Edge:
    u: int
    v: int
    distance_km: float
    speed_limit_kmh: float = 50.0
    capacity_vph: float = 1200.0  # vehicles per hour
    current_volume: float = 400.0
    gradient_percent: float = 0.0
    road_type: str = "primary"  # highway, primary, secondary, residential

    @property
    def free_flow_time_sec(self) -> float:
        speed_mps = (self.speed_limit_kmh * 1000.0) / 3600.0
        dist_m = self.distance_km * 1000.0
        return dist_m / max(0.1, speed_mps)


class RoadNetwork:
    """
    Weighted directed graph modeling urban transportation networks with dynamic traffic.
    """

    def __init__(self, name: str = "Urban Network"):
        self.name = name
        self.nodes: Dict[int, Node] = {}
        self.edges: Dict[Tuple[int, int], Edge] = {}
        self.adjacency: Dict[int, List[int]] = {}
        self.bpr_model = BPRCongestionModel()
        self.emission_model = CMEMEmissionModel()
        self.incidents: Dict[str, TrafficIncident] = {}
        self.weather: WeatherCondition = WeatherCondition.CLEAR
        self.sim_time: float = 28800.0  # default 8:00 AM in seconds

    def add_node(self, node: Node):
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = []

    def add_edge(self, edge: Edge, bidirectional: bool = True):
        self.edges[(edge.u, edge.v)] = edge
        if edge.u not in self.adjacency:
            self.adjacency[edge.u] = []
        if edge.v not in self.adjacency[edge.u]:
            self.adjacency[edge.u].append(edge.v)

        if bidirectional:
            reverse_edge = Edge(
                u=edge.v,
                v=edge.u,
                distance_km=edge.distance_km,
                speed_limit_kmh=edge.speed_limit_kmh,
                capacity_vph=edge.capacity_vph,
                current_volume=edge.current_volume,
                gradient_percent=-edge.gradient_percent,
                road_type=edge.road_type,
            )
            self.edges[(edge.v, edge.u)] = reverse_edge
            if edge.v not in self.adjacency:
                self.adjacency[edge.v] = []
            if edge.u not in self.adjacency[edge.v]:
                self.adjacency[edge.v].append(edge.u)

    def add_incident(self, incident: TrafficIncident):
        self.incidents[incident.incident_id] = incident

    def remove_incident(self, incident_id: str):
        if incident_id in self.incidents:
            del self.incidents[incident_id]

    def get_dynamic_edge_travel_time(self, u: int, v: int, current_time: Optional[float] = None) -> float:
        """
        Calculates time-dependent travel time on edge (u, v) in seconds.
        """
        if (u, v) not in self.edges:
            return float("inf")

        edge = self.edges[(u, v)]
        t = current_time if current_time is not None else self.sim_time

        # Calculate active incident delay if any
        incident_delay = 0.0
        for inc in self.incidents.values():
            if (inc.edge_u == u and inc.edge_v == v) or (inc.edge_u == v and inc.edge_v == u):
                incident_delay += inc.current_delay(t)

        # Rush hour surge multiplier
        surge = RushHourProfile.get_surge_multiplier(t)
        effective_volume = edge.current_volume * surge

        travel_time_sec = self.bpr_model.travel_time(
            free_flow_time=edge.free_flow_time_sec,
            volume=effective_volume,
            capacity=edge.capacity_vph,
            weather=self.weather,
            incident_delay=incident_delay,
        )
        return travel_time_sec

    def dijkstra_shortest_path(
        self, start_id: int, target_id: int, departure_time: float = 0.0
    ) -> Tuple[List[int], float, float]:
        """
        Finds shortest dynamic travel time path from start to target.
        Returns: (path_nodes, total_travel_time_sec, total_distance_km)
        """
        if start_id not in self.nodes or target_id not in self.nodes:
            return [], float("inf"), float("inf")

        if start_id == target_id:
            return [start_id], 0.0, 0.0

        distances: Dict[int, float] = {node_id: float("inf") for node_id in self.nodes}
        distances[start_id] = 0.0
        previous: Dict[int, Optional[int]] = {node_id: None for node_id in self.nodes}
        pq: List[Tuple[float, int]] = [(0.0, start_id)]

        while pq:
            curr_dist, curr_node = heapq.heappop(pq)
            if curr_dist > distances[curr_node]:
                continue
            if curr_node == target_id:
                break

            curr_time = departure_time + curr_dist
            for neighbor in self.adjacency.get(curr_node, []):
                edge_cost = self.get_dynamic_edge_travel_time(curr_node, neighbor, curr_time)
                new_dist = curr_dist + edge_cost
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = curr_node
                    heapq.heappush(pq, (new_dist, neighbor))

        if distances[target_id] == float("inf"):
            return [], float("inf"), float("inf")

        # Reconstruct path
        path: List[int] = []
        curr = target_id
        while curr is not None:
            path.append(curr)
            curr = previous[curr]
        path.reverse()

        # Calculate physical distance along path
        total_dist_km = 0.0
        for i in range(len(path) - 1):
            edge = self.edges.get((path[i], path[i + 1]))
            if edge:
                total_dist_km += edge.distance_km

        return path, distances[target_id], total_dist_km

    def compute_all_pairs_matrices(
        self, node_ids: List[int], departure_time: float = 0.0
    ) -> Tuple[List[List[float]], List[List[float]], Dict[Tuple[int, int], List[int]]]:
        """
        Computes (travel_time_matrix, distance_matrix, detailed_paths_dict)
        between specified node subsets (e.g. Depot + Customers).
        """
        n = len(node_ids)
        time_matrix = [[0.0] * n for _ in range(n)]
        dist_matrix = [[0.0] * n for _ in range(n)]
        paths: Dict[Tuple[int, int], List[int]] = {}

        for i, u in enumerate(node_ids):
            for j, v in enumerate(node_ids):
                if i == j:
                    time_matrix[i][j] = 0.0
                    dist_matrix[i][j] = 0.0
                    paths[(u, v)] = [u]
                else:
                    path, t_sec, d_km = self.dijkstra_shortest_path(u, v, departure_time)
                    time_matrix[i][j] = t_sec
                    dist_matrix[i][j] = d_km
                    paths[(u, v)] = path

        return time_matrix, dist_matrix, paths

    def to_dict(self) -> Dict[str, Any]:
        """Serializes network to JSON-compatible dictionary."""
        return {
            "name": self.name,
            "weather": self.weather.value,
            "sim_time": self.sim_time,
            "nodes": [
                {
                    "id": n.node_id,
                    "lat": n.lat,
                    "lon": n.lon,
                    "name": n.name,
                    "is_depot": n.is_depot,
                    "demand": n.demand,
                    "time_window_start": n.time_window_start,
                    "time_window_end": n.time_window_end,
                    "service_time": n.service_time,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "u": e.u,
                    "v": e.v,
                    "distance_km": e.distance_km,
                    "speed_limit_kmh": e.speed_limit_kmh,
                    "capacity_vph": e.capacity_vph,
                    "current_volume": e.current_volume,
                    "road_type": e.road_type,
                    "dynamic_time_sec": self.get_dynamic_edge_travel_time(e.u, e.v),
                }
                for e in self.edges.values()
            ],
            "incidents": [
                {
                    "id": inc.incident_id,
                    "edge_u": inc.edge_u,
                    "edge_v": inc.edge_v,
                    "severity": inc.severity,
                    "delay_seconds": inc.delay_seconds,
                    "start_time": inc.start_time,
                    "duration_seconds": inc.duration_seconds,
                    "description": inc.description,
                }
                for inc in self.incidents.values()
            ],
        }


# =====================================================================
# Pre-built City Map Generators
# =====================================================================

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def create_bengaluru_network() -> RoadNetwork:
    """Creates a realistic transportation graph of Bengaluru tech corridors."""
    net = RoadNetwork("Bengaluru Smart Hub Network")
    
    locations = [
        # (id, name, lat, lon, is_depot, demand, tw_start, tw_end)
        (0, "Central Logistics Hub (Majestic)", 12.9784, 77.5726, True, 0.0, 0, 86400),
        (1, "Koramangala 5th Block", 12.9352, 77.6245, False, 18.0, 28800, 36000),
        (2, "Indiranagar 100ft Rd", 12.9719, 77.6412, False, 22.0, 30000, 39600),
        (3, "Whitefield Tech Park", 12.9698, 77.7499, False, 35.0, 32400, 43200),
        (4, "Electronic City Phase 1", 12.8452, 77.6602, False, 40.0, 36000, 46800),
        (5, "HSR Layout Sector 1", 12.9121, 77.6446, False, 15.0, 28800, 36000),
        (6, "MG Road Metro Interchange", 12.9756, 77.6066, False, 12.0, 27000, 34200),
        (7, "Hebbal Flyover Junction", 13.0358, 77.5970, False, 28.0, 30600, 41400),
        (8, "Marathahalli Bridge", 12.9591, 77.6974, False, 30.0, 32400, 41400),
        (9, "Bellandur EcoSpace Hub", 12.9260, 77.6762, False, 32.0, 34200, 45000),
        (10, "BTM Layout 2nd Stage", 12.9166, 77.6101, False, 16.0, 28800, 37800),
        (11, "Jayanagar 4th Block", 12.9299, 77.5824, False, 20.0, 28800, 36000),
        (12, "Malleshwaram 8th Cross", 13.0031, 77.5701, False, 14.0, 27000, 34200),
        (13, "Rajajinagar Industrial Area", 12.9915, 77.5523, False, 25.0, 28800, 39600),
        (14, "Banashankari 2nd Stage", 12.9255, 77.5468, False, 19.0, 30600, 39600),
        (15, "Yelahanka New Town", 13.1007, 77.5963, False, 24.0, 36000, 48600),
    ]

    for node_data in locations:
        net.add_node(
            Node(
                node_id=node_data[0],
                name=node_data[1],
                lat=node_data[2],
                lon=node_data[3],
                is_depot=node_data[4],
                demand=node_data[5],
                time_window_start=float(node_data[6]),
                time_window_end=float(node_data[7]),
            )
        )

    # Key arterial connectivity
    road_connections = [
        (0, 6, "primary", 50, 1800, 1100),
        (0, 12, "primary", 45, 1400, 900),
        (0, 13, "primary", 50, 1500, 950),
        (0, 11, "primary", 50, 1600, 1050),
        (6, 2, "primary", 50, 1800, 1300),
        (2, 8, "primary", 50, 1700, 1400),
        (8, 3, "highway", 65, 2200, 1600),
        (8, 9, "primary", 45, 1600, 1500),
        (9, 5, "primary", 50, 1700, 1350),
        (5, 1, "primary", 45, 1500, 1200),
        (1, 6, "primary", 50, 1600, 1300),
        (1, 10, "secondary", 40, 1300, 950),
        (10, 4, "highway", 70, 2400, 1750),
        (5, 4, "highway", 70, 2400, 1650),
        (10, 11, "secondary", 40, 1200, 850),
        (11, 14, "secondary", 40, 1200, 800),
        (14, 13, "secondary", 40, 1200, 800),
        (12, 7, "highway", 60, 2000, 1400),
        (7, 15, "highway", 70, 2200, 1200),
        (6, 7, "primary", 55, 1900, 1350),
        (2, 7, "primary", 50, 1600, 1150),
    ]

    for u, v, rtype, spd, cap, vol in road_connections:
        n1 = net.nodes[u]
        n2 = net.nodes[v]
        dist = haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon)
        net.add_edge(
            Edge(
                u=u,
                v=v,
                distance_km=max(0.5, round(dist, 2)),
                speed_limit_kmh=spd,
                capacity_vph=cap,
                current_volume=vol,
                road_type=rtype,
            ),
            bidirectional=True,
        )

    return net


def create_delhi_network() -> RoadNetwork:
    """Creates a transportation network graph for Delhi NCR."""
    net = RoadNetwork("Delhi NCR Express Network")
    locations = [
        (0, "Central Freight Hub (Connaught Place)", 28.6315, 77.2167, True, 0.0, 0, 86400),
        (1, "Nehru Place Commercial Hub", 28.5494, 77.2539, False, 25.0, 28800, 36000),
        (2, "Cyber Hub Gurugram", 28.4950, 77.0895, False, 45.0, 32400, 43200),
        (3, "Noida Sector 62 Tech Zone", 28.6280, 77.3649, False, 38.0, 32400, 41400),
        (4, "Rohini Sector 10 Distribution", 28.7164, 77.1171, False, 20.0, 27000, 36000),
        (5, "Karol Bagh Market", 28.6517, 77.1906, False, 18.0, 28800, 34200),
        (6, "Dwarka Sector 21 Terminal", 28.5521, 77.0583, False, 30.0, 30600, 39600),
        (7, "South Extension II", 28.5686, 77.2188, False, 22.0, 28800, 37800),
        (8, "Okhla Industrial Phase III", 28.5355, 77.2711, False, 35.0, 32400, 45000),
        (9, "Lajpat Nagar Central Market", 28.5700, 77.2400, False, 15.0, 28800, 36000),
        (10, "Indirapuram Ghaziabad Link", 28.6415, 77.3712, False, 28.0, 34200, 46800),
        (11, "Aerocity Terminal Hub", 28.5511, 77.1215, False, 32.0, 28800, 37800),
    ]

    for node_data in locations:
        net.add_node(
            Node(
                node_id=node_data[0],
                name=node_data[1],
                lat=node_data[2],
                lon=node_data[3],
                is_depot=node_data[4],
                demand=node_data[5],
                time_window_start=float(node_data[6]),
                time_window_end=float(node_data[7]),
            )
        )

    conns = [
        (0, 5, "primary", 45, 1600, 1100),
        (0, 7, "primary", 55, 1800, 1300),
        (7, 1, "primary", 50, 1700, 1200),
        (7, 9, "secondary", 40, 1400, 950),
        (1, 8, "primary", 45, 1500, 1100),
        (1, 3, "highway", 70, 2200, 1600),
        (3, 10, "highway", 65, 2000, 1400),
        (0, 4, "primary", 55, 1800, 1200),
        (4, 5, "secondary", 45, 1400, 900),
        (0, 11, "highway", 70, 2400, 1600),
        (11, 2, "highway", 80, 2600, 1900),
        (11, 6, "primary", 60, 1900, 1300),
        (6, 2, "highway", 70, 2200, 1500),
        (7, 11, "primary", 60, 2000, 1400),
    ]

    for u, v, rtype, spd, cap, vol in conns:
        n1 = net.nodes[u]
        n2 = net.nodes[v]
        dist = haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon)
        net.add_edge(
            Edge(
                u=u,
                v=v,
                distance_km=max(0.5, round(dist, 2)),
                speed_limit_kmh=spd,
                capacity_vph=cap,
                current_volume=vol,
                road_type=rtype,
            ),
            bidirectional=True,
        )

    return net


def create_smart_grid_network(grid_size: int = 5) -> RoadNetwork:
    """Generates a synthetic grid city with arterial avenues and bottleneck bridges."""
    net = RoadNetwork(f"Smart Grid {grid_size}x{grid_size} City")
    base_lat, base_lon = 37.7749, -122.4194  # San Francisco coordinates base
    step = 0.015

    idx = 0
    for r in range(grid_size):
        for c in range(grid_size):
            is_depot = (r == 0 and c == 0)
            demand = 0.0 if is_depot else random.randint(10, 35)
            tw_s = 28800 + random.randint(0, 7200)
            tw_e = tw_s + random.randint(7200, 14400)
            net.add_node(
                Node(
                    node_id=idx,
                    name=f"Zone [{r},{c}]",
                    lat=base_lat + r * step,
                    lon=base_lon + c * step,
                    is_depot=is_depot,
                    demand=demand,
                    time_window_start=tw_s,
                    time_window_end=tw_e,
                )
            )
            idx += 1

    # Connect grid nodes
    for r in range(grid_size):
        for c in range(grid_size):
            u = r * grid_size + c
            # Right neighbor
            if c + 1 < grid_size:
                v = r * grid_size + (c + 1)
                net.add_edge(
                    Edge(
                        u=u,
                        v=v,
                        distance_km=1.8,
                        speed_limit_kmh=50.0,
                        capacity_vph=1400.0,
                        current_volume=random.uniform(400, 900),
                    )
                )
            # Down neighbor
            if r + 1 < grid_size:
                v = (r + 1) * grid_size + c
                net.add_edge(
                    Edge(
                        u=u,
                        v=v,
                        distance_km=1.8,
                        speed_limit_kmh=50.0,
                        capacity_vph=1400.0,
                        current_volume=random.uniform(400, 900),
                    )
                )

    return net
