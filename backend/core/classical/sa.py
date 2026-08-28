"""
Classical Simulated Annealing (SA) for VRP:
Standard Metropolis-Hastings thermal annealing baseline.
"""

import math
import random
import time
from typing import Any, Callable, Dict, List, Optional

from backend.core.vrp.problem import VRPProblem
from backend.core.vrp.solution import VRPEvaluator, VRPSolution


class ClassicalSASolver:
    """
    Classical Simulated Annealing (SA) Solver.
    """

    def __init__(
        self,
        problem: VRPProblem,
        max_iterations: int = 3000,
        initial_temp: float = 150.0,
        cooling_rate: float = 0.995,
        seed: Optional[int] = None,
    ):
        self.problem = problem
        self.max_iterations = max_iterations
        self.t0 = initial_temp
        self.cooling_rate = cooling_rate
        self.evaluator = VRPEvaluator(problem)

        if seed is not None:
            random.seed(seed)

    def _get_neighbor(self, permutation: List[int]) -> List[int]:
        if len(permutation) <= 2:
            return list(reversed(permutation))

        neighbor = list(permutation)
        op = random.random()

        if op < 0.5:
            # Swap
            i, j = random.sample(range(len(permutation)), 2)
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
        else:
            # 2-Opt / Inversion
            i, j = sorted(random.sample(range(len(permutation)), 2))
            neighbor[i:j + 1] = reversed(neighbor[i:j + 1])

        return neighbor

    def solve(
        self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> VRPSolution:
        start_time = time.perf_counter()

        customer_ids = [c.customer_id for c in self.problem.customers]
        if not customer_ids:
            sol = self.evaluator.evaluate_routes([])
            sol.algorithm_name = "Classical SA"
            return sol

        current_perm = list(customer_ids)
        random.shuffle(current_perm)
        current_routes = self.evaluator.decode_permutation_to_routes(current_perm)
        current_eval = self.evaluator.evaluate_routes(current_routes)
        current_fitness = current_eval.fitness_score

        best_perm = list(current_perm)
        best_fitness = current_fitness
        best_routes = current_routes

        temp = self.t0
        convergence_history: List[float] = []

        for step in range(self.max_iterations):
            temp = self.t0 * (self.cooling_rate ** step)

            neighbor_perm = self._get_neighbor(current_perm)
            neighbor_routes = self.evaluator.decode_permutation_to_routes(neighbor_perm)
            neighbor_eval = self.evaluator.evaluate_routes(neighbor_routes)
            neighbor_fitness = neighbor_eval.fitness_score

            delta_e = neighbor_fitness - current_fitness

            # Classical Metropolis acceptance
            if delta_e < 0 or (random.random() < math.exp(-delta_e / max(1e-4, temp))):
                current_perm = neighbor_perm
                current_fitness = neighbor_fitness
                current_routes = neighbor_routes

                if current_fitness < best_fitness:
                    best_fitness = current_fitness
                    best_perm = list(current_perm)
                    best_routes = current_routes

            convergence_history.append(float(best_fitness))

            if progress_callback and (step % 100 == 0 or step == self.max_iterations - 1):
                progress_callback(
                    {
                        "step": step + 1,
                        "max_steps": self.max_iterations,
                        "best_fitness": float(best_fitness),
                        "temperature": float(temp),
                    }
                )

        final_sol = self.evaluator.evaluate_routes(best_routes)
        final_sol.algorithm_name = "Classical SA"
        final_sol.computation_time_ms = (time.perf_counter() - start_time) * 1000.0
        final_sol.convergence_history = convergence_history

        return final_sol
