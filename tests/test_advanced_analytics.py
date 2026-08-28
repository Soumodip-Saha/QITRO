"""
Unit Tests for Advanced Analytics, Hypothesis Testing, Scalability, and Convergence Profiling
"""

import pytest
from backend.core.graph.network import create_bengaluru_network
from backend.core.vrp.problem import VRPProblem, ProblemType, Customer, Vehicle, OptimizationWeights
from backend.core.benchmarking.advanced_analytics import (
    StatisticalHypothesisTester,
    ConvergenceProfiler,
    ScalabilityProfiler,
    QuantumTheoryMetadata,
)


@pytest.fixture
def sample_problem():
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
        problem_id="analytics_test",
        name="Analytics Test VRP",
        problem_type=ProblemType.VRPTW,
        depot_node_id=depot_id,
        customers=customers,
        fleet=fleet,
        time_matrix=time_mat,
        dist_matrix=dist_mat,
        detailed_paths=paths,
        weights=OptimizationWeights(),
    )


def test_hypothesis_tester():
    q_scores = [100.0, 98.5, 102.0, 99.0, 101.5, 97.8]
    c_scores = [125.0, 130.0, 122.5, 128.0, 135.0, 126.4]

    res = StatisticalHypothesisTester.run_paired_tests(q_scores, c_scores)
    assert res["num_trials"] == 6
    assert res["cohens_d"] > 0.8
    assert res["wilcoxon"]["is_significant"] is True
    assert res["paired_ttest"]["is_significant"] is True
    assert res["mann_whitney_u"]["is_significant"] is True


def test_convergence_profiler(sample_problem):
    profile = ConvergenceProfiler.profile_convergence(
        sample_problem,
        algorithm_key="QPSO",
        num_runs=3,
        max_iterations=20,
    )
    assert profile is not None
    assert len(profile["iterations"]) == 20
    assert len(profile["mean_fitness"]) == 20
    assert len(profile["upper_band_1sigma"]) == 20
    assert len(profile["lower_band_1sigma"]) == 20
    assert len(profile["alpha_trajectory"]) == 20
    assert len(profile["quantum_entropy"]) == 20
    assert profile["summary"]["total_improvement_pct"] >= 0.0


def test_scalability_profiler():
    profile = ScalabilityProfiler.profile_scalability(node_sizes=[5, 10])
    assert profile is not None
    assert len(profile["scaling_data"]) == 2
    assert "qpso_runtime_ms" in profile["scaling_data"][0]
    assert "theoretical_complexity" in profile


def test_quantum_theory_metadata():
    theory = QuantumTheoryMetadata.get_mathematical_foundations()
    assert "quantum_potential_well" in theory
    assert "quantum_genetic_mechanics" in theory
    assert "quantum_annealing_tunneling" in theory
    assert "bpr_congestion_formulation" in theory
    assert "cmem_emissions_formulation" in theory
