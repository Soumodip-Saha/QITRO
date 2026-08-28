"""
Baseline Heuristic Solvers:
- Greedy Nearest Neighbor
- Clarke-Wright Savings Algorithm
"""

import time
from typing import Any, Callable, Dict, List, Optional

from backend.core.vrp.problem import VRPProblem
from backend.core.vrp.solution import VRPEvaluator, VRPSolution


class GreedyNearestNeighborSolver:
    """
    Greedy Nearest Neighbor Heuristic.
    """

    def __init__(self, problem: VRPProblem):
        self.problem = problem
        self.evaluator = VRPEvaluator(problem)

    def solve(
        self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> VRPSolution:
        start_time = time.perf_counter()

        unvisited = set(c.customer_id for c in self.problem.customers)
        routes: List[List[int]] = []

        for vehicle in self.problem.fleet:
            if not unvisited:
                break

            curr_route: List[int] = []
            curr_load = 0.0
            curr_pos = 0  # depot

            while unvisited:
                # Find closest customer that satisfies capacity
                candidates = [
                    (cid, self.problem.time_matrix[curr_pos][cid])
                    for cid in unvisited
                    if curr_load + self.problem.customer_map[cid].demand <= vehicle.capacity
                ]

                if not candidates:
                    # Vehicle full, return to depot
                    break

                closest_cid = min(candidates, key=lambda x: x[1])[0]
                curr_route.append(closest_cid)
                curr_load += self.problem.customer_map[closest_cid].demand
                unvisited.remove(closest_cid)
                curr_pos = closest_cid

            if curr_route:
                routes.append(curr_route)

        # Pad remaining vehicles if needed
        while len(routes) < len(self.problem.fleet):
            routes.append([])

        sol = self.evaluator.evaluate_routes(routes)
        sol.unassigned_customers = list(unvisited)
        sol.algorithm_name = "Greedy Nearest Neighbor"
        sol.computation_time_ms = (time.perf_counter() - start_time) * 1000.0
        sol.convergence_history = [sol.fitness_score]

        return sol


class ClarkeWrightSavingsSolver:
    """
    Clarke-Wright Savings Algorithm for CVRP.
    """

    def __init__(self, problem: VRPProblem):
        self.problem = problem
        self.evaluator = VRPEvaluator(problem)

    def solve(
        self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> VRPSolution:
        start_time = time.perf_counter()

        customers = [c.customer_id for c in self.problem.customers]
        if not customers:
            sol = self.evaluator.evaluate_routes([])
            sol.algorithm_name = "Clarke-Wright Savings"
            return sol

        # Compute savings s_ij = c_0i + c_0j - c_ij
        savings = []
        for i in range(len(customers)):
            ci = customers[i]
            for j in range(i + 1, len(customers)):
                cj = customers[j]
                s = (
                    self.problem.dist_matrix[0][ci]
                    + self.problem.dist_matrix[0][cj]
                    - self.problem.dist_matrix[ci][cj]
                )
                savings.append((s, ci, cj))

        savings.sort(key=lambda x: x[0], reverse=True)

        # Initialize: one route per customer [0 -> i -> 0]
        routes: Dict[int, List[int]] = {c: [c] for c in customers}
        loads: Dict[int, float] = {c: self.problem.customer_map[c].demand for c in customers}
        route_of: Dict[int, int] = {c: c for c in customers}

        max_cap = self.problem.fleet[0].capacity if self.problem.fleet else 100.0

        for s, i, j in savings:
            r_i = route_of[i]
            r_j = route_of[j]

            if r_i == r_j:
                continue

            route_i = routes[r_i]
            route_j = routes[r_j]

            # Merge condition: i must be endpoint of route_i, j endpoint of route_j, and total demand <= capacity
            can_merge = False
            merged_list: List[int] = []

            if route_i[-1] == i and route_j[0] == j:
                if loads[r_i] + loads[r_j] <= max_cap:
                    can_merge = True
                    merged_list = route_i + route_j
            elif route_i[0] == i and route_j[-1] == j:
                if loads[r_i] + loads[r_j] <= max_cap:
                    can_merge = True
                    merged_list = route_j + route_i
            elif route_i[-1] == i and route_j[-1] == j:
                if loads[r_i] + loads[r_j] <= max_cap:
                    can_merge = True
                    merged_list = route_i + list(reversed(route_j))
            elif route_i[0] == i and route_j[0] == j:
                if loads[r_i] + loads[r_j] <= max_cap:
                    can_merge = True
                    merged_list = list(reversed(route_i)) + route_j

            if can_merge:
                new_load = loads[r_i] + loads[r_j]
                del routes[r_i]
                del routes[r_j]
                routes[r_i] = merged_list
                loads[r_i] = new_load

                for node in merged_list:
                    route_of[node] = r_i

        final_raw_routes = list(routes.values())
        while len(final_raw_routes) < len(self.problem.fleet):
            final_raw_routes.append([])

        sol = self.evaluator.evaluate_routes(final_raw_routes[: len(self.problem.fleet)])
        sol.algorithm_name = "Clarke-Wright Savings"
        sol.computation_time_ms = (time.perf_counter() - start_time) * 1000.0
        sol.convergence_history = [sol.fitness_score]

        return sol
