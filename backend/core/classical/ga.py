"""
Classical Genetic Algorithm (GA) for VRP:
Classical baseline with Order Crossover (OX), Swap Mutation,
and Tournament Selection.
"""

import random
import time
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from backend.core.vrp.problem import VRPProblem
from backend.core.vrp.solution import VRPEvaluator, VRPSolution


class ClassicalGASolver:
    """
    Classical Genetic Algorithm (GA) Solver.
    """

    def __init__(
        self,
        problem: VRPProblem,
        population_size: int = 40,
        pop_size: Optional[int] = None,
        max_generations: int = 150,
        crossover_rate: float = 0.85,
        mutation_rate: float = 0.15,
        tournament_size: int = 4,
        elitism_count: int = 2,
        seed: Optional[int] = None,
        **kwargs,
    ):
        self.problem = problem
        self.pop_size = pop_size if pop_size is not None else population_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.elitism_count = elitism_count
        self.evaluator = VRPEvaluator(problem)
        self.num_dim = problem.num_customers

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def _order_crossover(self, parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
        """Order Crossover (OX) for permutation chromosomes."""
        size = len(parent1)
        if size <= 2:
            return list(parent1), list(parent2)

        cx1, cx2 = sorted(random.sample(range(size), 2))

        def _ox_child(p1: List[int], p2: List[int]) -> List[int]:
            child = [None] * size
            child[cx1:cx2 + 1] = p1[cx1:cx2 + 1]
            p1_set = set(child[cx1:cx2 + 1])

            p2_filtered = [item for item in p2 if item not in p1_set]
            fill_idx = (cx2 + 1) % size

            for item in p2_filtered:
                while child[fill_idx] is not None:
                    fill_idx = (fill_idx + 1) % size
                child[fill_idx] = item

            return [item for item in child if item is not None]

        child1 = _ox_child(parent1, parent2)
        child2 = _ox_child(parent2, parent1)
        return child1, child2

    def _mutate(self, chromosome: List[int]) -> List[int]:
        """Swap / Inversion mutation."""
        if len(chromosome) <= 2:
            return chromosome

        mutated = list(chromosome)
        if random.random() < self.mutation_rate:
            if random.random() < 0.5:
                # Swap mutation
                i, j = random.sample(range(len(chromosome)), 2)
                mutated[i], mutated[j] = mutated[j], mutated[i]
            else:
                # Inversion mutation
                i, j = sorted(random.sample(range(len(chromosome)), 2))
                mutated[i:j + 1] = reversed(mutated[i:j + 1])
        return mutated

    def solve(
        self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> VRPSolution:
        start_time = time.perf_counter()

        customer_ids = [c.customer_id for c in self.problem.customers]
        if not customer_ids:
            sol = self.evaluator.evaluate_routes([])
            sol.algorithm_name = "Classical GA"
            return sol

        # Initialize Population
        population: List[List[int]] = []
        for _ in range(self.pop_size):
            chrom = list(customer_ids)
            random.shuffle(chrom)
            population.append(chrom)

        best_chromosome = list(population[0])
        best_fitness = float("inf")
        best_routes: List[List[int]] = []

        convergence_history: List[float] = []

        for gen in range(self.max_generations):
            fitness_scores = []
            all_routes = []

            for chrom in population:
                routes = self.evaluator.decode_permutation_to_routes(chrom)
                sol = self.evaluator.evaluate_routes(routes)
                fitness_scores.append(sol.fitness_score)
                all_routes.append(routes)

                if sol.fitness_score < best_fitness:
                    best_fitness = sol.fitness_score
                    best_chromosome = list(chrom)
                    best_routes = routes

            convergence_history.append(float(best_fitness))

            # Tournament Selection
            def _select() -> List[int]:
                candidates = random.sample(range(self.pop_size), self.tournament_size)
                winner_idx = min(candidates, key=lambda idx: fitness_scores[idx])
                return population[winner_idx]

            # Elitism: retain top individuals
            sorted_indices = sorted(range(self.pop_size), key=lambda idx: fitness_scores[idx])
            new_population = [list(population[i]) for i in sorted_indices[: self.elitism_count]]

            # Generate Offspring
            while len(new_population) < self.pop_size:
                p1 = _select()
                p2 = _select()

                if random.random() < self.crossover_rate:
                    c1, c2 = self._order_crossover(p1, p2)
                else:
                    c1, c2 = list(p1), list(p2)

                c1 = self._mutate(c1)
                c2 = self._mutate(c2)

                new_population.append(c1)
                if len(new_population) < self.pop_size:
                    new_population.append(c2)

            population = new_population

            if progress_callback and (gen % 5 == 0 or gen == self.max_generations - 1):
                progress_callback(
                    {
                        "generation": gen + 1,
                        "max_generations": self.max_generations,
                        "best_fitness": float(best_fitness),
                    }
                )

        final_sol = self.evaluator.evaluate_routes(best_routes)
        final_sol.algorithm_name = "Classical GA"
        final_sol.computation_time_ms = (time.perf_counter() - start_time) * 1000.0
        final_sol.convergence_history = convergence_history

        return final_sol
