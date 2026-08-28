"""
Unit Tests for Classical Metaheuristic & Baseline Algorithms
"""

import pytest
from backend.core.graph.network import create_bengaluru_network
from backend.core.vrp.problem import VRPProblem, ProblemType, Customer, Vehicle, OptimizationWeights
from backend.core.classical.pso import ClassicalPSOSolver
from backend.core.classical.ga import ClassicalGASolver
from backend.core.classical.sa import ClassicalSASolver
from backend.core.classical.baselines import (
    GreedyNearestNeighborSolver,
    ClarkeWrightSavingsSolver,
)


@pytest.fixture
def sample_vrp_problem():
    network = create_bengaluru_network()
    depot_id = 0
    customers = [
        Customer(
            customer_id=idx + 1,
            node_id=n.node_id,
            name=n.name,
            lat=n.lat,
            lon=n.lon,
            demand=n.demand,
            time_window_start=n.time_window_start,
            time_window_end=n.time_window_end,
            service_time=n.service_time,
        )
        for idx, n in enumerate(list(network.nodes.values())[1:7])
    ]
    node_ids = [depot_id] + [c.node_id for c in customers]
    time_mat, dist_mat, paths = network.compute_all_pairs_matrices(node_ids, 28800.0)
    fleet = [Vehicle(vehicle_id=1, capacity=80.0), Vehicle(vehicle_id=2, capacity=80.0)]

    return VRPProblem(
        problem_id="test_prob",
        name="Test VRP",
        problem_type=ProblemType.VRPTW,
        depot_node_id=depot_id,
        customers=customers,
        fleet=fleet,
        time_matrix=time_mat,
        dist_matrix=dist_mat,
        detailed_paths=paths,
        weights=OptimizationWeights(),
    )


def test_classical_pso(sample_vrp_problem):
    solver = ClassicalPSOSolver(sample_vrp_problem, swarm_size=20, max_iterations=30, seed=42)
    sol = solver.solve()
    assert sol is not None
    assert sol.fitness_score < float("inf")
    assert len(sol.convergence_history) == 30


def test_classical_ga(sample_vrp_problem):
    solver = ClassicalGASolver(sample_vrp_problem, pop_size=20, max_generations=30, seed=42)
    sol = solver.solve()
    assert sol is not None
    assert sol.fitness_score < float("inf")
    assert len(sol.convergence_history) == 30


def test_classical_sa(sample_vrp_problem):
    solver = ClassicalSASolver(sample_vrp_problem, max_iterations=500, seed=42)
    sol = solver.solve()
    assert sol is not None
    assert sol.fitness_score < float("inf")


def test_greedy_baseline(sample_vrp_problem):
    solver = GreedyNearestNeighborSolver(sample_vrp_problem)
    sol = solver.solve()
    assert sol is not None
    assert sol.total_distance_km > 0.0


def test_clarke_wright_baseline(sample_vrp_problem):
    solver = ClarkeWrightSavingsSolver(sample_vrp_problem)
    sol = solver.solve()
    assert sol is not None
    assert sol.total_distance_km > 0.0
