"""
Benchmarking Runner:
Executes multiple algorithms across problem instances with multiple seeds,
collects convergence trajectories, and produces structured comparative reports.
"""

from typing import Any, Callable, Dict, List, Optional
import time

from backend.core.vrp.problem import VRPProblem
from backend.core.vrp.solution import VRPSolution
from backend.core.quantum.qpso import QPSOSolver
from backend.core.quantum.qga import QGASolver
from backend.core.quantum.qsa import QSASolver
from backend.core.classical.pso import ClassicalPSOSolver
from backend.core.classical.ga import ClassicalGASolver
from backend.core.classical.sa import ClassicalSASolver
from backend.core.classical.baselines import (
    GreedyNearestNeighborSolver,
    ClarkeWrightSavingsSolver,
)
from backend.core.benchmarking.statistics import (
    BenchmarkStatistics,
    BenchmarkMetricSummary,
)


class BenchmarkRunner:
    """
    Orchestrates systematic benchmarking across quantum and classical algorithms.
    """

    AVAILABLE_ALGORITHMS = {
        "QPSO": QPSOSolver,
        "QGA": QGASolver,
        "QSA": QSASolver,
        "PSO": ClassicalPSOSolver,
        "GA": ClassicalGASolver,
        "SA": ClassicalSASolver,
        "GREEDY": GreedyNearestNeighborSolver,
        "CLARKE_WRIGHT": ClarkeWrightSavingsSolver,
    }

    def __init__(self, problem: VRPProblem):
        self.problem = problem

    def run_single(
        self,
        algorithm_key: str,
        params: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        seed: Optional[int] = 42,
    ) -> VRPSolution:
        if algorithm_key not in self.AVAILABLE_ALGORITHMS:
            raise ValueError(f"Unknown algorithm key '{algorithm_key}'. Available: {list(self.AVAILABLE_ALGORITHMS.keys())}")

        solver_cls = self.AVAILABLE_ALGORITHMS[algorithm_key]
        kwargs = dict(params or {})
        if "seed" not in kwargs and solver_cls not in (GreedyNearestNeighborSolver, ClarkeWrightSavingsSolver):
            kwargs["seed"] = seed

        solver = solver_cls(self.problem, **kwargs)
        sol = solver.solve(progress_callback=progress_callback)
        return sol

    def run_full_benchmark(
        self,
        algorithm_keys: Optional[List[str]] = None,
        num_runs: int = 5,
        iterations_override: Optional[int] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Runs comprehensive benchmark suite across selected algorithms with multiple independent runs.
        """
        if algorithm_keys is None:
            algorithm_keys = ["QPSO", "QGA", "PSO", "GA", "CLARKE_WRIGHT"]

        results_by_algo: Dict[str, List[Dict[str, Any]]] = {}
        solutions_by_algo: Dict[str, List[VRPSolution]] = {}
        best_solution_by_algo: Dict[str, VRPSolution] = {}

        total_tasks = len(algorithm_keys) * num_runs
        task_count = 0

        for algo_key in algorithm_keys:
            results_by_algo[algo_key] = []
            solutions_by_algo[algo_key] = []
            best_sol: Optional[VRPSolution] = None

            params = {}
            if iterations_override:
                if algo_key in ("QPSO", "PSO"):
                    params["max_iterations"] = iterations_override
                elif algo_key in ("QGA", "GA"):
                    params["max_generations"] = iterations_override
                elif algo_key in ("QSA", "SA"):
                    params["max_iterations"] = iterations_override * 15

            # Deterministic runs if heuristic baseline
            actual_runs = 1 if algo_key in ("GREEDY", "CLARKE_WRIGHT") else num_runs

            for run_idx in range(actual_runs):
                seed = 100 + run_idx * 37
                sol = self.run_single(algo_key, params=params, seed=seed)
                sol_dict = sol.to_dict()

                results_by_algo[algo_key].append(sol_dict)
                solutions_by_algo[algo_key].append(sol)

                if best_sol is None or sol.fitness_score < best_sol.fitness_score:
                    best_sol = sol

                task_count += 1
                if progress_callback:
                    progress_callback(
                        {
                            "current_algo": algo_key,
                            "run_index": run_idx + 1,
                            "total_runs": actual_runs,
                            "progress_pct": round((task_count / total_tasks) * 100.0, 1),
                        }
                    )

            if best_sol:
                best_solution_by_algo[algo_key] = best_sol

        # Statistical Summaries
        summaries: Dict[str, BenchmarkMetricSummary] = {}
        for algo_key, run_list in results_by_algo.items():
            algo_name = best_solution_by_algo[algo_key].algorithm_name if algo_key in best_solution_by_algo else algo_key
            summaries[algo_key] = BenchmarkStatistics.summarize_runs(algo_name, run_list)

        # Pairwise Statistical Significance Tests & Comparisons
        comparisons = []
        wilcoxon_tests = {}

        if "QPSO" in summaries and "PSO" in summaries:
            qpso_scores = [r["fitness_score"] for r in results_by_algo["QPSO"]]
            pso_scores = [r["fitness_score"] for r in results_by_algo["PSO"]]
            wilcoxon_tests["QPSO_vs_PSO"] = BenchmarkStatistics.calculate_wilcoxon_test(qpso_scores, pso_scores)
            comparisons.append(BenchmarkStatistics.compare_algorithms(summaries["QPSO"], summaries["PSO"]))

        if "QGA" in summaries and "GA" in summaries:
            qga_scores = [r["fitness_score"] for r in results_by_algo["QGA"]]
            ga_scores = [r["fitness_score"] for r in results_by_algo["GA"]]
            wilcoxon_tests["QGA_vs_GA"] = BenchmarkStatistics.calculate_wilcoxon_test(qga_scores, ga_scores)
            comparisons.append(BenchmarkStatistics.compare_algorithms(summaries["QGA"], summaries["GA"]))

        if "QPSO" in summaries and "CLARKE_WRIGHT" in summaries:
            comparisons.append(BenchmarkStatistics.compare_algorithms(summaries["QPSO"], summaries["CLARKE_WRIGHT"]))

        # Format Final Benchmark Payload
        return {
            "problem_name": self.problem.name,
            "problem_type": self.problem.problem_type.value,
            "num_customers": self.problem.num_customers,
            "num_vehicles": self.problem.num_vehicles,
            "num_runs_per_algo": num_runs,
            "summaries": {
                k: {
                    "algorithm_name": v.algorithm_name,
                    "fitness_mean": round(v.fitness_mean, 4),
                    "fitness_std": round(v.fitness_std, 4),
                    "fitness_best": round(v.fitness_best, 4),
                    "fitness_worst": round(v.fitness_worst, 4),
                    "distance_mean_km": round(v.distance_mean_km, 2),
                    "travel_time_mean_sec": round(v.travel_time_mean_sec, 1),
                    "co2_mean_kg": round(v.co2_mean_kg, 3),
                    "fuel_mean_liters": round(v.fuel_mean_liters, 2),
                    "computation_time_mean_ms": round(v.computation_time_mean_ms, 2),
                    "feasibility_rate_pct": round(v.feasibility_rate * 100.0, 1),
                    "box_plot": v.box_plot_data,
                }
                for k, v in summaries.items()
            },
            "comparisons": comparisons,
            "wilcoxon_significance": wilcoxon_tests,
            "best_solutions": {
                k: v.to_dict() for k, v in best_solution_by_algo.items()
            },
            "convergence_curves": {
                k: best_solution_by_algo[k].convergence_history
                for k in best_solution_by_algo
                if len(best_solution_by_algo[k].convergence_history) > 1
            },
        }
