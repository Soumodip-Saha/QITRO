"""
VRP Problem Definition:
Defines CVRP, VRPTW, and DVRP problem models with vehicle capacities,
delivery time windows, customer demands, and multi-objective configurations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


class ProblemType(str, Enum):
    CVRP = "CVRP"          # Capacitated Vehicle Routing Problem
    VRPTW = "VRPTW"        # VRP with Time Windows
    DVRP = "DVRP"          # Dynamic VRP with Live Congestion & Detours


@dataclass
class Customer:
    customer_id: int          # Index in problem (1..N)
    node_id: int              # Node ID in graph
    name: str
    lat: float
    lon: float
    demand: float
    time_window_start: float  # seconds from start of day
    time_window_end: float    # seconds from start of day
    service_time: float = 300.0  # seconds


@dataclass
class Vehicle:
    vehicle_id: int
    capacity: float = 100.0
    max_travel_time_sec: float = 28800.0  # 8 hours max shift
    speed_factor: float = 1.0
    cost_per_km: float = 1.2
    cost_per_hour: float = 25.0


@dataclass
class OptimizationWeights:
    weight_travel_time: float = 0.40
    weight_distance: float = 0.25
    weight_emissions: float = 0.20
    weight_capacity_penalty: float = 1000.0
    weight_time_window_penalty: float = 50.0  # penalty per second of violation


class VRPProblem:
    """
    Encapsulates all problem data, cost matrices, constraints, and parameters.
    """

    def __init__(
        self,
        problem_id: str,
        name: str,
        problem_type: ProblemType,
        depot_node_id: int,
        customers: List[Customer],
        fleet: List[Vehicle],
        time_matrix: List[List[float]],
        dist_matrix: List[List[float]],
        detailed_paths: Optional[Dict[Tuple[int, int], List[int]]] = None,
        weights: Optional[OptimizationWeights] = None,
        start_time_sec: float = 28800.0,  # 08:00 AM
    ):
        self.problem_id = problem_id
        self.name = name
        self.problem_type = problem_type
        self.depot_node_id = depot_node_id
        self.customers = customers
        self.fleet = fleet
        self.time_matrix = time_matrix
        self.dist_matrix = dist_matrix
        self.detailed_paths = detailed_paths or {}
        self.weights = weights or OptimizationWeights()
        self.start_time_sec = start_time_sec

        # Fast lookup mapping: customer_id (1..N) -> Customer
        self.customer_map: Dict[int, Customer] = {c.customer_id: c for c in self.customers}
        # Mapping: node_id -> customer_id (0 for depot)
        self.node_to_idx: Dict[int, int] = {c.node_id: c.customer_id for c in self.customers}
        self.node_to_idx[self.depot_node_id] = 0

    @property
    def num_customers(self) -> int:
        return len(self.customers)

    @property
    def num_vehicles(self) -> int:
        return len(self.fleet)

    @property
    def total_demand(self) -> float:
        return sum(c.demand for c in self.customers)

    @property
    def total_capacity(self) -> float:
        return sum(v.capacity for v in self.fleet)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "name": self.name,
            "problem_type": self.problem_type.value,
            "depot_node_id": self.depot_node_id,
            "num_customers": self.num_customers,
            "num_vehicles": self.num_vehicles,
            "total_demand": self.total_demand,
            "total_capacity": self.total_capacity,
            "customers": [
                {
                    "customer_id": c.customer_id,
                    "node_id": c.node_id,
                    "name": c.name,
                    "lat": c.lat,
                    "lon": c.lon,
                    "demand": c.demand,
                    "time_window_start": c.time_window_start,
                    "time_window_end": c.time_window_end,
                    "service_time": c.service_time,
                }
                for c in self.customers
            ],
            "fleet": [
                {
                    "vehicle_id": v.vehicle_id,
                    "capacity": v.capacity,
                    "max_travel_time_sec": v.max_travel_time_sec,
                }
                for v in self.fleet
            ],
        }
