"""
Classical Standard Particle Swarm Optimization (PSO) for VRP:
Classical baseline with inertia weight (w), cognitive acceleration (c1),
and social acceleration (c2) velocity vectors.
"""

import random
import time
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from backend.core.vrp.problem import VRPProblem
from backend.core.vrp.solution import VRPEvaluator, VRPSolution


class ClassicalPSOSolver:
    """
    Standard Classical Particle Swarm Optimization (PSO) Solver.
    """

    def __init__(
        self,
        problem: VRPProblem,
        swarm_size: int = 40,
        max_iterations: int = 150,
        w_max: float = 0.9,
        w_min: float = 0.4,
        c1: float = 2.0,
        c2: float = 2.0,
        v_max: float = 4.0,
        seed: Optional[int] = None,
    ):
        self.problem = problem
        self.swarm_size = swarm_size
        self.max_iterations = max_iterations
        self.w_max = w_max
        self.w_min = w_min
        self.c1 = c1
        self.c2 = c2
        self.v_max = v_max
        self.evaluator = VRPEvaluator(problem)
        self.num_dim = problem.num_customers

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def _rov_decode(self, continuous_pos: np.ndarray) -> List[int]:
        customer_ids = [c.customer_id for c in self.problem.customers]
        sorted_indices = np.argsort(continuous_pos)
        return [customer_ids[idx] for idx in sorted_indices]

    def solve(
        self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> VRPSolution:
        start_time = time.perf_counter()

        if self.num_dim == 0:
            sol = self.evaluator.evaluate_routes([])
            sol.algorithm_name = "Classical PSO"
            return sol

        # Positions and Velocities
        X = np.random.uniform(-5.0, 5.0, size=(self.swarm_size, self.num_dim))
        V = np.random.uniform(-self.v_max, self.v_max, size=(self.swarm_size, self.num_dim))

        P = np.copy(X)
        P_fitness = np.full(self.swarm_size, float("inf"))

        g_best_pos = np.copy(X[0])
        g_best_fitness = float("inf")
        g_best_routes: List[List[int]] = []

        convergence_history: List[float] = []

        for i in range(self.swarm_size):
            perm = self._rov_decode(X[i])
            routes = self.evaluator.decode_permutation_to_routes(perm)
            sol = self.evaluator.evaluate_routes(routes)

            P_fitness[i] = sol.fitness_score
            if sol.fitness_score < g_best_fitness:
                g_best_fitness = sol.fitness_score
                g_best_pos = np.copy(X[i])
                g_best_routes = routes

        for t in range(self.max_iterations):
            # Dynamic inertia weight
            w = self.w_max - ((self.w_max - self.w_min) * t / self.max_iterations)

            r1 = np.random.uniform(0.0, 1.0, size=(self.swarm_size, self.num_dim))
            r2 = np.random.uniform(0.0, 1.0, size=(self.swarm_size, self.num_dim))

            # Classical velocity update: V = w*V + c1*r1*(P - X) + c2*r2*(G - X)
            V = w * V + self.c1 * r1 * (P - X) + self.c2 * r2 * (g_best_pos - X)
            V = np.clip(V, -self.v_max, self.v_max)

            # Position update: X = X + V
            X = X + V
            X = np.clip(X, -10.0, 10.0)

            for i in range(self.swarm_size):
                perm = self._rov_decode(X[i])
                routes = self.evaluator.decode_permutation_to_routes(perm)
                sol = self.evaluator.evaluate_routes(routes)

                if sol.fitness_score < P_fitness[i]:
                    P_fitness[i] = sol.fitness_score
                    P[i] = np.copy(X[i])

                    if sol.fitness_score < g_best_fitness:
                        g_best_fitness = sol.fitness_score
                        g_best_pos = np.copy(X[i])
                        g_best_routes = routes

            convergence_history.append(float(g_best_fitness))

            if progress_callback and (t % 5 == 0 or t == self.max_iterations - 1):
                progress_callback(
                    {
                        "iteration": t + 1,
                        "max_iterations": self.max_iterations,
                        "best_fitness": float(g_best_fitness),
                        "inertia_w": float(w),
                    }
                )

        final_sol = self.evaluator.evaluate_routes(g_best_routes)
        final_sol.algorithm_name = "Classical PSO"
        final_sol.computation_time_ms = (time.perf_counter() - start_time) * 1000.0
        final_sol.convergence_history = convergence_history

        return final_sol
