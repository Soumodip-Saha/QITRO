"""
VRP Solution & Objective Evaluator:
Calculates multi-objective fitness, route metrics, capacity violations,
time-window penalties, waiting times, and carbon emissions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from backend.core.vrp.problem import VRPProblem, ProblemType
from backend.core.graph.traffic_models import CMEMEmissionModel


@dataclass
class StopInfo:
    customer_id: int
    node_id: int
    arrival_time_sec: float
    service_start_sec: float
    departure_time_sec: float
    waiting_time_sec: float
    time_window_violation_sec: float
    accumulated_load: float
    accumulated_distance_km: float


@dataclass
class Route:
    vehicle_id: int
    customer_ids: List[int]  # Ordered sequence of customer_ids (1..N)
    total_distance_km: float = 0.0
    total_travel_time_sec: float = 0.0
    total_service_time_sec: float = 0.0
    total_waiting_time_sec: float = 0.0
    total_tw_violation_sec: float = 0.0
    total_load: float = 0.0
    capacity_violation: float = 0.0
    co2_grams: float = 0.0
    fuel_liters: float = 0.0
    stops: List[StopInfo] = field(default_factory=list)
    detailed_node_path: List[int] = field(default_factory=list)

    @property
    def is_feasible(self) -> bool:
        return self.capacity_violation <= 1e-6 and self.total_tw_violation_sec <= 1e-6


@dataclass
class VRPSolution:
    routes: List[Route]
    fitness_score: float = float("inf")
    total_distance_km: float = 0.0
    total_travel_time_sec: float = 0.0
    total_service_time_sec: float = 0.0
    total_waiting_time_sec: float = 0.0
    total_tw_violation_sec: float = 0.0
    total_capacity_violation: float = 0.0
    total_co2_grams: float = 0.0
    total_fuel_liters: float = 0.0
    unassigned_customers: List[int] = field(default_factory=list)
    is_feasible: bool = False
    algorithm_name: str = ""
    computation_time_ms: float = 0.0
    convergence_history: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm_name": self.algorithm_name,
            "fitness_score": round(self.fitness_score, 4),
            "is_feasible": self.is_feasible,
            "total_distance_km": round(self.total_distance_km, 2),
            "total_travel_time_sec": round(self.total_travel_time_sec, 1),
            "total_service_time_sec": round(self.total_service_time_sec, 1),
            "total_waiting_time_sec": round(self.total_waiting_time_sec, 1),
            "total_tw_violation_sec": round(self.total_tw_violation_sec, 1),
            "total_capacity_violation": round(self.total_capacity_violation, 2),
            "total_co2_kg": round(self.total_co2_grams / 1000.0, 3),
            "total_fuel_liters": round(self.total_fuel_liters, 2),
            "computation_time_ms": round(self.computation_time_ms, 2),
            "num_active_routes": len([r for r in self.routes if len(r.customer_ids) > 0]),
            "unassigned_customers": self.unassigned_customers,
            "routes": [
                {
                    "vehicle_id": r.vehicle_id,
                    "customer_ids": r.customer_ids,
                    "total_distance_km": round(r.total_distance_km, 2),
                    "total_travel_time_sec": round(r.total_travel_time_sec, 1),
                    "total_load": round(r.total_load, 1),
                    "capacity_violation": round(r.capacity_violation, 1),
                    "tw_violation_sec": round(r.total_tw_violation_sec, 1),
                    "co2_kg": round(r.co2_grams / 1000.0, 3),
                    "fuel_liters": round(r.fuel_liters, 2),
                    "detailed_node_path": r.detailed_node_path,
                    "stops": [
                        {
                            "customer_id": s.customer_id,
                            "node_id": s.node_id,
                            "arrival_time_sec": round(s.arrival_time_sec, 1),
                            "departure_time_sec": round(s.departure_time_sec, 1),
                            "waiting_time_sec": round(s.waiting_time_sec, 1),
                            "violation_sec": round(s.time_window_violation_sec, 1),
                            "accumulated_load": round(s.accumulated_load, 1),
                        }
                        for s in r.stops
                    ],
                }
                for r in self.routes
            ],
            "convergence_history": [round(f, 4) for f in self.convergence_history],
        }


class VRPEvaluator:
    """
    Evaluates customer permutations or structured routes into a full VRPSolution.
    """

    def __init__(self, problem: VRPProblem):
        self.problem = problem
        self.emission_model = CMEMEmissionModel()

    def evaluate_routes(self, raw_routes: List[List[int]]) -> VRPSolution:
        """
        raw_routes: List of lists of customer_ids (1..N), one list per vehicle.
        """
        evaluated_routes: List[Route] = []
        total_dist = 0.0
        total_travel_time = 0.0
        total_service_time = 0.0
        total_waiting_time = 0.0
        total_tw_violation = 0.0
        total_cap_violation = 0.0
        total_co2 = 0.0
        total_fuel = 0.0

        for v_idx, cust_list in enumerate(raw_routes):
            if v_idx >= len(self.problem.fleet):
                # Extra unserved routes
                continue

            vehicle = self.problem.fleet[v_idx]
            route = Route(vehicle_id=vehicle.vehicle_id, customer_ids=cust_list)
            
            if not cust_list:
                evaluated_routes.append(route)
                continue

            curr_matrix_idx = 0  # 0 is depot
            curr_time = self.problem.start_time_sec
            curr_load = 0.0
            accum_dist = 0.0
            detailed_path = [self.problem.depot_node_id]

            for cust_id in cust_list:
                customer = self.problem.customer_map[cust_id]
                next_matrix_idx = cust_id

                # Travel from curr to next
                travel_time = self.problem.time_matrix[curr_matrix_idx][next_matrix_idx]
                leg_dist = self.problem.dist_matrix[curr_matrix_idx][next_matrix_idx]

                route.total_travel_time_sec += travel_time
                route.total_distance_km += leg_dist
                accum_dist += leg_dist
                curr_time += travel_time
                curr_load += customer.demand

                # Calculate speed and emissions for this leg
                mean_speed = (leg_dist / max(1.0, travel_time / 3600.0)) if travel_time > 0 else 50.0
                emissions = self.emission_model.calculate_emissions(leg_dist, mean_speed)
                route.co2_grams += emissions["co2_grams"]
                route.fuel_liters += emissions["fuel_liters"]

                # Detailed graph path tracking
                u_node = self.problem.depot_node_id if curr_matrix_idx == 0 else self.problem.customer_map[curr_matrix_idx].node_id
                v_node = customer.node_id
                leg_nodes = self.problem.detailed_paths.get((u_node, v_node), [v_node])
                if leg_nodes and leg_nodes[0] == detailed_path[-1]:
                    detailed_path.extend(leg_nodes[1:])
                else:
                    detailed_path.extend(leg_nodes)

                # Time window analysis
                arrival_time = curr_time
                waiting_time = 0.0
                violation = 0.0

                if arrival_time < customer.time_window_start:
                    waiting_time = customer.time_window_start - arrival_time
                    service_start = customer.time_window_start
                else:
                    service_start = arrival_time
                    if arrival_time > customer.time_window_end:
                        violation = arrival_time - customer.time_window_end

                departure_time = service_start + customer.service_time
                curr_time = departure_time
                route.total_service_time_sec += customer.service_time
                route.total_waiting_time_sec += waiting_time
                route.total_tw_violation_sec += violation

                route.stops.append(
                    StopInfo(
                        customer_id=customer.customer_id,
                        node_id=customer.node_id,
                        arrival_time_sec=arrival_time,
                        service_start_sec=service_start,
                        departure_time_sec=departure_time,
                        waiting_time_sec=waiting_time,
                        time_window_violation_sec=violation,
                        accumulated_load=curr_load,
                        accumulated_distance_km=accum_dist,
                    )
                )

                curr_matrix_idx = next_matrix_idx

            # Return from last customer back to depot
            return_travel_time = self.problem.time_matrix[curr_matrix_idx][0]
            return_dist = self.problem.dist_matrix[curr_matrix_idx][0]
            route.total_travel_time_sec += return_travel_time
            route.total_distance_km += return_dist
            
            mean_speed_ret = (return_dist / max(1.0, return_travel_time / 3600.0)) if return_travel_time > 0 else 50.0
            ret_emissions = self.emission_model.calculate_emissions(return_dist, mean_speed_ret)
            route.co2_grams += ret_emissions["co2_grams"]
            route.fuel_liters += ret_emissions["fuel_liters"]

            last_node = self.problem.customer_map[curr_matrix_idx].node_id
            return_nodes = self.problem.detailed_paths.get((last_node, self.problem.depot_node_id), [self.problem.depot_node_id])
            if return_nodes and return_nodes[0] == detailed_path[-1]:
                detailed_path.extend(return_nodes[1:])
            else:
                detailed_path.extend(return_nodes)
            route.detailed_node_path = detailed_path

            # Capacity violation
            route.total_load = curr_load
            if curr_load > vehicle.capacity:
                route.capacity_violation = curr_load - vehicle.capacity

            # Max shift duration check (overtime penalty)
            total_duration = curr_time + return_travel_time - self.problem.start_time_sec
            if total_duration > vehicle.max_travel_time_sec:
                route.total_tw_violation_sec += (total_duration - vehicle.max_travel_time_sec)

            evaluated_routes.append(route)

            total_dist += route.total_distance_km
            total_travel_time += route.total_travel_time_sec
            total_service_time += route.total_service_time_sec
            total_waiting_time += route.total_waiting_time_sec
            total_tw_violation += route.total_tw_violation_sec
            total_cap_violation += route.capacity_violation
            total_co2 += route.co2_grams
            total_fuel += route.fuel_liters

        # Calculate overall fitness score
        w = self.problem.weights
        fitness = (
            w.weight_travel_time * (total_travel_time / 60.0)  # in minutes
            + w.weight_distance * total_dist                   # in km
            + w.weight_emissions * (total_co2 / 1000.0)        # in kg CO2
            + w.weight_capacity_penalty * total_cap_violation
            + w.weight_time_window_penalty * (total_tw_violation / 60.0)
        )

        is_feasible = (total_cap_violation <= 1e-6) and (total_tw_violation <= 1e-6)

        return VRPSolution(
            routes=evaluated_routes,
            fitness_score=fitness,
            total_distance_km=total_dist,
            total_travel_time_sec=total_travel_time,
            total_service_time_sec=total_service_time,
            total_waiting_time_sec=total_waiting_time,
            total_tw_violation_sec=total_tw_violation,
            total_capacity_violation=total_cap_violation,
            total_co2_grams=total_co2,
            total_fuel_liters=total_fuel,
            is_feasible=is_feasible,
        )

    def decode_permutation_to_routes(self, permutation: List[int]) -> List[List[int]]:
        """
        Splits a permutation of all customer_ids into vehicle routes using
        balanced capacity and travel horizon constraints.
        """
        num_v = len(self.problem.fleet)
        routes: List[List[int]] = [[] for _ in range(num_v)]
        if not permutation:
            return routes

        v_idx = 0
        curr_load = 0.0
        curr_time = self.problem.start_time_sec
        curr_node = 0

        for cust_id in permutation:
            if cust_id not in self.problem.customer_map:
                continue
            demand = self.problem.customer_map[cust_id].demand
            service = self.problem.customer_map[cust_id].service_time
            travel_time = self.problem.time_matrix[curr_node][cust_id]
            ret_travel_time = self.problem.time_matrix[cust_id][0]

            v_cap = self.problem.fleet[v_idx].capacity
            v_max_time = self.problem.fleet[v_idx].max_travel_time_sec

            proj_load = curr_load + demand
            proj_duration = (curr_time + travel_time + service + ret_travel_time) - self.problem.start_time_sec

            if (proj_load <= v_cap and proj_duration <= v_max_time) or (v_idx >= num_v - 1):
                routes[v_idx].append(cust_id)
                curr_load += demand
                curr_time += (travel_time + service)
                curr_node = cust_id
            else:
                # Open next vehicle
                v_idx += 1
                routes[v_idx].append(cust_id)
                curr_load = demand
                curr_time = self.problem.start_time_sec + self.problem.time_matrix[0][cust_id] + service
                curr_node = cust_id

        return routes
