"""
Quantum Genetic Algorithm (QGA) for VRP:
Embeds quantum computing principles:
- Q-bit chromosome representation [alpha, beta]^T with |alpha|^2 + |beta|^2 = 1
- Quantum Superposition measurement and state collapse
- Quantum Rotation Gate U(Delta theta) with adaptive lookup tables
- Pauli-X Quantum NOT mutation
- Quantum Catastrophe phase-shift diversity injection
"""

import math
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from backend.core.vrp.problem import VRPProblem
from backend.core.vrp.solution import VRPEvaluator, VRPSolution


class QGASolver:
    """
    Quantum Genetic Algorithm (QGA) Solver.
    """

    def __init__(
        self,
        problem: VRPProblem,
        population_size: int = 40,
        max_generations: int = 150,
        mutation_rate: float = 0.05,
        rotation_step_base: float = 0.03 * math.pi,
        catastrophe_threshold: float = 0.02,
        seed: Optional[int] = None,
    ):
        self.problem = problem
        self.pop_size = population_size
        self.max_generations = max_generations
        self.mutation_rate = mutation_rate
        self.rotation_step_base = rotation_step_base
        self.catastrophe_threshold = catastrophe_threshold
        self.evaluator = VRPEvaluator(problem)
        self.num_dim = problem.num_customers

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def _initialize_q_chromosomes(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Initializes Q-bit population in equal superposition:
        alpha = 1/sqrt(2), beta = 1/sqrt(2) (angles theta = pi/4)
        """
        # Theta representation: alpha = cos(theta), beta = sin(theta)
        # Guarantees alpha^2 + beta^2 = 1 strictly.
        theta = np.full((self.pop_size, self.num_dim), math.pi / 4.0)
        return theta

    def _collapse_and_decode(self, theta: np.ndarray) -> Tuple[np.ndarray, List[List[int]]]:
        """
        Observes/collapses quantum states based on probability |beta|^2 = sin^2(theta)
        and converts continuous probabilities to customer permutations.
        """
        beta_squared = np.sin(theta) ** 2
        # Stochastic observation with quantum noise
        observed_continuous = beta_squared + np.random.normal(0, 0.05, size=theta.shape)
        
        customer_ids = [c.customer_id for c in self.problem.customers]
        permutations = []
        for i in range(self.pop_size):
            sorted_idx = np.argsort(observed_continuous[i])
            perm = [customer_ids[idx] for idx in sorted_idx]
            permutations.append(perm)

        return observed_continuous, permutations

    def _apply_rotation_gates(
        self,
        theta: np.ndarray,
        fitnesses: np.ndarray,
        best_theta: np.ndarray,
        best_fitness: float,
        generation: int,
    ) -> np.ndarray:
        """
        Applies Quantum Rotation Gate: theta_new = theta + Delta_theta
        where Delta_theta direction guides individuals toward the global best state.
        """
        # Dynamic rotation step size (decays as generations advance)
        decay = 1.0 - 0.7 * (generation / max(1, self.max_generations))
        step = self.rotation_step_base * decay

        new_theta = np.copy(theta)
        for i in range(self.pop_size):
            if fitnesses[i] <= best_fitness + 1e-6:
                # Elite doesn't rotate away
                continue

            # Quantum rotation table heuristic:
            # If current state angle < best state angle, rotate positively (+step)
            # Else rotate negatively (-step)
            diff = best_theta - theta[i]
            delta_theta = np.sign(diff) * step
            # Add stochastic quantum tunneling component
            delta_theta += np.random.normal(0, 0.1 * step, size=self.num_dim)

            new_theta[i] = theta[i] + delta_theta

        # Keep theta within [0, pi/2] for positive quadrant rotation
        new_theta = np.clip(new_theta, 0.001, (math.pi / 2.0) - 0.001)
        return new_theta

    def _apply_pauli_x_mutation(self, theta: np.ndarray) -> np.ndarray:
        """
        Pauli-X (Quantum NOT) Mutation:
        Swaps alpha and beta: theta -> (pi/2 - theta)
        """
        mutated_theta = np.copy(theta)
        mask = np.random.uniform(0.0, 1.0, size=theta.shape) < self.mutation_rate
        mutated_theta[mask] = (math.pi / 2.0) - mutated_theta[mask]
        return mutated_theta

    def _quantum_catastrophe(self, theta: np.ndarray) -> np.ndarray:
        """
        Quantum Catastrophe / Phase Diversity Injection:
        If quantum diversity drops too low, inject phase diversity to 80% of the population.
        """
        pop_diversity = np.mean(np.std(theta, axis=0))
        if pop_diversity < self.catastrophe_threshold:
            # Re-scramble non-elite chromosomes with random phase shifts
            for i in range(1, self.pop_size):
                theta[i] = np.random.uniform(0.05, (math.pi / 2.0) - 0.05, size=self.num_dim)
        return theta

    def solve(
        self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> VRPSolution:
        start_time = time.perf_counter()

        if self.num_dim == 0:
            sol = self.evaluator.evaluate_routes([])
            sol.algorithm_name = "QGA"
            return sol

        # Initialize Q-bit population
        theta = self._initialize_q_chromosomes()

        best_theta = np.copy(theta[0])
        best_fitness = float("inf")
        best_routes: List[List[int]] = []

        convergence_history: List[float] = []

        for gen in range(self.max_generations):
            # Superposition collapse & Permutation decoding
            _, permutations = self._collapse_and_decode(theta)

            fitnesses = np.zeros(self.pop_size)
            current_routes = []

            for i in range(self.pop_size):
                routes = self.evaluator.decode_permutation_to_routes(permutations[i])
                sol = self.evaluator.evaluate_routes(routes)
                fitnesses[i] = sol.fitness_score
                current_routes.append(routes)

                if sol.fitness_score < best_fitness:
                    best_fitness = sol.fitness_score
                    best_theta = np.copy(theta[i])
                    best_routes = routes

            convergence_history.append(float(best_fitness))

            # Apply Quantum Rotation Gates
            theta = self._apply_rotation_gates(theta, fitnesses, best_theta, best_fitness, gen)

            # Apply Pauli-X Quantum Mutation
            theta = self._apply_pauli_x_mutation(theta)

            # Apply Quantum Catastrophe / Phase Diversity
            theta = self._quantum_catastrophe(theta)

            # Ensure elite preservation
            theta[0] = np.copy(best_theta)

            if progress_callback and (gen % 5 == 0 or gen == self.max_generations - 1):
                alpha_probs = np.cos(best_theta) ** 2
                beta_probs = np.sin(best_theta) ** 2
                progress_callback(
                    {
                        "generation": gen + 1,
                        "max_generations": self.max_generations,
                        "best_fitness": float(best_fitness),
                        "mean_alpha_prob": float(np.mean(alpha_probs)),
                        "mean_beta_prob": float(np.mean(beta_probs)),
                        "quantum_diversity": float(np.mean(np.std(theta, axis=0))),
                    }
                )

        final_sol = self.evaluator.evaluate_routes(best_routes)
        final_sol.algorithm_name = "QGA (Quantum Genetic)"
        final_sol.computation_time_ms = (time.perf_counter() - start_time) * 1000.0
        final_sol.convergence_history = convergence_history

        return final_sol
