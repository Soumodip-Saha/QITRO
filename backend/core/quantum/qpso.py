"""
Quantum-behaved Particle Swarm Optimization (QPSO) for VRP:
Embeds quantum mechanics principles:
- Wave function in a delta-potential well centered at local attractor p
- Mean Best Position (mbest) collective intelligence
- Adaptive Contraction-Expansion (CE) alpha schedule
- Ranked Order Value (ROV) permutation decoding
- Quantum state inspection (dispersion, potential well width, phase-space entropy)
"""

import math
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from backend.core.vrp.problem import VRPProblem
from backend.core.vrp.solution import VRPEvaluator, VRPSolution


class QPSOSolver:
    """
    Quantum-behaved Particle Swarm Optimization (QPSO) Solver.
    """

    def __init__(
        self,
        problem: VRPProblem,
        swarm_size: int = 40,
        max_iterations: int = 150,
        alpha_max: float = 1.0,
        alpha_min: float = 0.4,
        local_search_freq: int = 10,
        seed: Optional[int] = None,
    ):
        self.problem = problem
        self.swarm_size = swarm_size
        self.max_iterations = max_iterations
        self.alpha_max = alpha_max
        self.alpha_min = alpha_min
        self.local_search_freq = local_search_freq
        self.evaluator = VRPEvaluator(problem)
        self.num_dim = problem.num_customers  # Dimension equals number of customers

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def _rov_decode(self, continuous_pos: np.ndarray) -> List[int]:
        """
        Ranked Order Value (ROV) mapping:
        Sorts continuous position dimensions into a permutation of customer_ids (1..N).
        """
        customer_ids = [c.customer_id for c in self.problem.customers]
        # Sort customer IDs based on the values in continuous_pos
        sorted_indices = np.argsort(continuous_pos)
        permutation = [customer_ids[idx] for idx in sorted_indices]
        return permutation

    def _apply_2opt(self, routes: List[List[int]]) -> List[List[int]]:
        """
        2-Opt local search improvement for individual routes.
        """
        improved_routes = []
        for route in routes:
            if len(route) <= 3:
                improved_routes.append(route)
                continue

            best_route = list(route)
            improved = True
            count = 0
            while improved and count < 15:
                improved = False
                count += 1
                for i in range(len(best_route) - 1):
                    for j in range(i + 2, len(best_route) + 1):
                        new_route = best_route[:i] + best_route[i:j][::-1] + best_route[j:]
                        # Fast cost check
                        old_eval = self.evaluator.evaluate_routes([best_route])
                        new_eval = self.evaluator.evaluate_routes([new_route])
                        if new_eval.fitness_score < old_eval.fitness_score - 1e-4:
                            best_route = new_route
                            improved = True
                            break
                    if improved:
                        break
            improved_routes.append(best_route)
        return improved_routes

    def solve(
        self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> VRPSolution:
        start_time = time.perf_counter()

        if self.num_dim == 0:
            sol = self.evaluator.evaluate_routes([])
            sol.algorithm_name = "QPSO"
            return sol

        # Initialize Swarm positions in continuous domain [-5.0, 5.0]
        # X: (swarm_size, num_dim)
        X = np.random.uniform(-5.0, 5.0, size=(self.swarm_size, self.num_dim))
        
        # P: Personal best positions
        P = np.copy(X)
        P_fitness = np.full(self.swarm_size, float("inf"))
        P_routes: List[List[List[int]]] = [[] for _ in range(self.swarm_size)]

        # Global best
        g_best_pos = np.copy(X[0])
        g_best_fitness = float("inf")
        g_best_routes: List[List[int]] = []

        convergence_history: List[float] = []
        quantum_entropy_history: List[float] = []

        # Evaluate initial swarm
        for i in range(self.swarm_size):
            perm = self._rov_decode(X[i])
            routes = self.evaluator.decode_permutation_to_routes(perm)
            sol = self.evaluator.evaluate_routes(routes)

            P_fitness[i] = sol.fitness_score
            P_routes[i] = routes

            if sol.fitness_score < g_best_fitness:
                g_best_fitness = sol.fitness_score
                g_best_pos = np.copy(X[i])
                g_best_routes = routes

        # Iterative Quantum Evolution
        for t in range(self.max_iterations):
            # Dynamic Contraction-Expansion (CE) coefficient
            alpha = self.alpha_max - ((self.alpha_max - self.alpha_min) * t / self.max_iterations)

            # Compute Mean Best Position (mbest) across all personal bests
            mbest = np.mean(P, axis=0)

            # Calculate quantum phase-space dispersion / entropy
            pos_std = np.mean(np.std(X, axis=0))
            quantum_entropy = float(pos_std)
            quantum_entropy_history.append(quantum_entropy)

            for i in range(self.swarm_size):
                # Random stochastic weights phi for local attractor
                phi = np.random.uniform(0.0, 1.0, size=self.num_dim)
                # Local attractor center p_ij
                p_i = phi * P[i] + (1.0 - phi) * g_best_pos

                # Monte Carlo sampling of wave function in delta-potential well
                u = np.random.uniform(0.0001, 0.9999, size=self.num_dim)
                sign = np.where(np.random.uniform(0.0, 1.0, size=self.num_dim) > 0.5, 1.0, -1.0)
                
                # Quantum delta-potential well position update:
                # X_ij(t+1) = p_ij +- alpha * |mbest_j - X_ij| * ln(1/u)
                quantum_step = alpha * np.abs(mbest - X[i]) * np.log(1.0 / u)
                X[i] = p_i + sign * quantum_step

                # Clamp to domain
                X[i] = np.clip(X[i], -10.0, 10.0)

                # Decode to permutation and evaluate
                perm = self._rov_decode(X[i])
                routes = self.evaluator.decode_permutation_to_routes(perm)
                
                # Periodic 2-opt local search enhancement
                if (t % self.local_search_freq == 0) and (i % 5 == 0):
                    routes = self._apply_2opt(routes)

                sol = self.evaluator.evaluate_routes(routes)

                # Update Personal Best
                if sol.fitness_score < P_fitness[i]:
                    P_fitness[i] = sol.fitness_score
                    P[i] = np.copy(X[i])
                    P_routes[i] = routes

                    # Update Global Best
                    if sol.fitness_score < g_best_fitness:
                        g_best_fitness = sol.fitness_score
                        g_best_pos = np.copy(X[i])
                        g_best_routes = routes

            convergence_history.append(float(g_best_fitness))

            # Progress callback streaming for UI
            if progress_callback and (t % 5 == 0 or t == self.max_iterations - 1):
                progress_callback(
                    {
                        "iteration": t + 1,
                        "max_iterations": self.max_iterations,
                        "best_fitness": float(g_best_fitness),
                        "alpha": float(alpha),
                        "mbest_norm": float(np.linalg.norm(mbest)),
                        "quantum_dispersion": float(pos_std),
                    }
                )

        # Final evaluation of the global best routes
        final_sol = self.evaluator.evaluate_routes(g_best_routes)
        final_sol.algorithm_name = "QPSO (Quantum Swarm)"
        final_sol.computation_time_ms = (time.perf_counter() - start_time) * 1000.0
        final_sol.convergence_history = convergence_history

        return final_sol
