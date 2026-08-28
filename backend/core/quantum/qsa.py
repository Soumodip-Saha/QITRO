"""
Quantum Simulated Annealing (QSA) for VRP:
Embeds quantum tunneling principles:
- Transverse-field fluctuation Gamma(t) decaying alongside temperature T(t)
- Quantum tunneling acceptance probability allowing rapid escape from narrow local minima
- Multi-neighborhood quantum hopping (Swap, Inversion, 2-Opt, Relocate)
"""

import math
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from backend.core.vrp.problem import VRPProblem
from backend.core.vrp.solution import VRPEvaluator, VRPSolution


class QSASolver:
    """
    Quantum Simulated Annealing (QSA) Solver.
    """

    def __init__(
        self,
        problem: VRPProblem,
        max_iterations: int = 3000,
        initial_temp: float = 150.0,
        cooling_rate: float = 0.995,
        initial_gamma: float = 80.0,  # Quantum transverse tunneling field
        seed: Optional[int] = None,
    ):
        self.problem = problem
        self.max_iterations = max_iterations
        self.t0 = initial_temp
        self.cooling_rate = cooling_rate
        self.gamma0 = initial_gamma
        self.evaluator = VRPEvaluator(problem)
        self.num_dim = problem.num_customers

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def _get_neighbor(self, permutation: List[int]) -> List[int]:
        """Applies stochastic neighborhood operator (Swap, Inversion, Insertion)."""
        if len(permutation) <= 2:
            return list(reversed(permutation))

        neighbor = list(permutation)
        op = random.random()

        if op < 0.40:
            # 2-Opt / Inversion
            i, j = sorted(random.sample(range(len(permutation)), 2))
            neighbor[i:j + 1] = reversed(neighbor[i:j + 1])
        elif op < 0.75:
            # Swap
            i, j = random.sample(range(len(permutation)), 2)
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
        else:
            # Relocate / Insertion
            i, j = random.sample(range(len(permutation)), 2)
            val = neighbor.pop(i)
            neighbor.insert(j, val)

        return neighbor

    def solve(
        self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> VRPSolution:
        start_time = time.perf_counter()

        customer_ids = [c.customer_id for c in self.problem.customers]
        if not customer_ids:
            sol = self.evaluator.evaluate_routes([])
            sol.algorithm_name = "QSA"
            return sol

        # Initial random state
        current_perm = list(customer_ids)
        random.shuffle(current_perm)
        current_routes = self.evaluator.decode_permutation_to_routes(current_perm)
        current_eval = self.evaluator.evaluate_routes(current_routes)
        current_fitness = current_eval.fitness_score

        best_perm = list(current_perm)
        best_fitness = current_fitness
        best_routes = current_routes

        temp = self.t0
        gamma = self.gamma0
        convergence_history: List[float] = []

        for step in range(self.max_iterations):
            # Dynamic annealing & quantum field decay
            t_decay = 1.0 - (step / self.max_iterations)
            temp = self.t0 * (self.cooling_rate ** step)
            gamma = self.gamma0 * (t_decay ** 1.5)

            # Generate candidate neighbor
            neighbor_perm = self._get_neighbor(current_perm)
            neighbor_routes = self.evaluator.decode_permutation_to_routes(neighbor_perm)
            neighbor_eval = self.evaluator.evaluate_routes(neighbor_routes)
            neighbor_fitness = neighbor_eval.fitness_score

            delta_e = neighbor_fitness - current_fitness

            # Quantum tunneling acceptance probability:
            # P_accept = min(1, exp(-DeltaE / T) + tanh(Gamma / (T + 1e-4)))
            accept = False
            if delta_e < 0:
                accept = True
            else:
                thermal_prob = math.exp(-delta_e / max(1e-4, temp))
                # Quantum tunneling factor: enables hopping across barrier when Gamma > 0
                tunneling_factor = math.tanh(gamma / max(1e-4, temp + 10.0)) * 0.4
                quantum_prob = min(1.0, thermal_prob + tunneling_factor)
                if random.random() < quantum_prob:
                    accept = True

            if accept:
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
                        "quantum_gamma": float(gamma),
                    }
                )

        final_sol = self.evaluator.evaluate_routes(best_routes)
        final_sol.algorithm_name = "QSA (Quantum Annealing)"
        final_sol.computation_time_ms = (time.perf_counter() - start_time) * 1000.0
        final_sol.convergence_history = convergence_history

        return final_sol
