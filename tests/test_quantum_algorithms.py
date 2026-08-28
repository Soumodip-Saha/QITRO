"""
Unit Tests for Quantum-Inspired Metaheuristic Algorithms (QPSO, QGA, QSA)
"""

import pytest
from backend.core.graph.network import create_bengaluru_network
from backend.core.vrp.problem import VRPProblem, ProblemType, Customer, Vehicle, OptimizationWeights
from backend.core.quantum.qpso import QPSOSolver
from backend.core.quantum.qga import QGASolver
from backend.core.quantum.qsa import QSASolver


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
        for idx, n in enumerate(list(network.nodes.values())[1:7])  # 6 customers
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


def test_qpso_solver(sample_vrp_problem):
    solver = QPSOSolver(sample_vrp_problem, swarm_size=20, max_iterations=40, seed=42)
    sol = solver.solve()

    assert sol is not None
    assert sol.fitness_score < float("inf")
    assert sol.total_distance_km > 0.0
    assert len(sol.convergence_history) == 40
    # Convergence must be non-increasing for best fitness
    for i in range(1, len(sol.convergence_history)):
        assert sol.convergence_history[i] <= sol.convergence_history[i - 1] + 1e-6


def test_qga_solver(sample_vrp_problem):
    solver = QGASolver(sample_vrp_problem, population_size=20, max_generations=35, seed=42)
    sol = solver.solve()

    assert sol is not None
    assert sol.fitness_score < float("inf")
    assert sol.total_distance_km > 0.0
    assert len(sol.convergence_history) == 35


def test_qsa_solver(sample_vrp_problem):
    solver = QSASolver(sample_vrp_problem, max_iterations=500, seed=42)
    sol = solver.solve()

    assert sol is not None
    assert sol.fitness_score < float("inf")
    assert sol.total_distance_km > 0.0
    assert len(sol.convergence_history) == 500
