"""
Unit Tests for Benchmark Suite and Statistical Analytics
"""

import pytest
from backend.core.graph.network import create_bengaluru_network
from backend.core.vrp.problem import VRPProblem, ProblemType, Customer, Vehicle, OptimizationWeights
from backend.core.benchmarking.runner import BenchmarkRunner
from backend.core.benchmarking.statistics import BenchmarkStatistics, BenchmarkMetricSummary


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
        for idx, n in enumerate(list(network.nodes.values())[1:6])
    ]
    node_ids = [depot_id] + [c.node_id for c in customers]
    time_mat, dist_mat, paths = network.compute_all_pairs_matrices(node_ids, 28800.0)
    fleet = [Vehicle(vehicle_id=1, capacity=80.0), Vehicle(vehicle_id=2, capacity=80.0)]

    return VRPProblem(
        problem_id="bench_prob",
        name="Benchmark VRP",
        problem_type=ProblemType.VRPTW,
        depot_node_id=depot_id,
        customers=customers,
        fleet=fleet,
        time_matrix=time_mat,
        dist_matrix=dist_mat,
        detailed_paths=paths,
        weights=OptimizationWeights(),
    )


def test_full_benchmark_execution(sample_vrp_problem):
    runner = BenchmarkRunner(sample_vrp_problem)
    report = runner.run_full_benchmark(
        algorithm_keys=["QPSO", "PSO", "CLARKE_WRIGHT"],
        num_runs=3,
        iterations_override=25,
    )

    assert report is not None
    assert "summaries" in report
    assert "QPSO" in report["summaries"]
    assert "PSO" in report["summaries"]
    assert "CLARKE_WRIGHT" in report["summaries"]
    assert "convergence_curves" in report
    assert "wilcoxon_significance" in report


def test_wilcoxon_calculation():
    # Synthetic samples where quantum is strictly better
    quantum_scores = [120.0, 118.5, 122.0, 119.0, 121.2]
    classical_scores = [145.0, 150.2, 142.8, 148.0, 155.1]

    res = BenchmarkStatistics.calculate_wilcoxon_test(quantum_scores, classical_scores)
    assert res["is_significant"] is True
    assert res["p_value"] < 0.05
