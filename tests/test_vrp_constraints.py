"""
Unit Tests for VRP Constraints, Capacity Limits, Time Windows, and Emissions
"""

from backend.core.vrp.problem import VRPProblem, ProblemType, Customer, Vehicle, OptimizationWeights
from backend.core.vrp.solution import VRPEvaluator, VRPSolution
from backend.core.graph.traffic_models import CMEMEmissionModel, BPRCongestionModel, WeatherCondition


def test_capacity_penalty_calculation():
    # Setup problem with 1 customer having demand = 100 on vehicle capacity = 50
    customer = Customer(
        customer_id=1,
        node_id=1,
        name="Heavy Customer",
        lat=12.0,
        lon=77.0,
        demand=100.0,
        time_window_start=0.0,
        time_window_end=86400.0,
    )
    fleet = [Vehicle(vehicle_id=1, capacity=50.0)]
    time_mat = [[0.0, 100.0], [100.0, 0.0]]
    dist_mat = [[0.0, 10.0], [10.0, 0.0]]

    prob = VRPProblem(
        problem_id="cap_test",
        name="Capacity Test",
        problem_type=ProblemType.CVRP,
        depot_node_id=0,
        customers=[customer],
        fleet=fleet,
        time_matrix=time_mat,
        dist_matrix=dist_mat,
        weights=OptimizationWeights(weight_capacity_penalty=500.0),
    )

    evaluator = VRPEvaluator(prob)
    sol = evaluator.evaluate_routes([[1]])

    assert not sol.is_feasible
    assert sol.total_capacity_violation == 50.0  # 100 - 50
    assert sol.fitness_score >= 50.0 * 500.0


def test_time_window_violation_calculation():
    customer = Customer(
        customer_id=1,
        node_id=1,
        name="Strict Window Customer",
        lat=12.0,
        lon=77.0,
        demand=10.0,
        time_window_start=28800.0,
        time_window_end=29000.0,  # Closes at 29000
    )
    fleet = [Vehicle(vehicle_id=1, capacity=50.0)]
    # Travel time takes 1000s from start=28800 -> arrival at 29800 (violation = 800s)
    time_mat = [[0.0, 1000.0], [1000.0, 0.0]]
    dist_mat = [[0.0, 10.0], [10.0, 0.0]]

    prob = VRPProblem(
        problem_id="tw_test",
        name="TW Test",
        problem_type=ProblemType.VRPTW,
        depot_node_id=0,
        customers=[customer],
        fleet=fleet,
        time_matrix=time_mat,
        dist_matrix=dist_mat,
        start_time_sec=28800.0,
    )

    evaluator = VRPEvaluator(prob)
    sol = evaluator.evaluate_routes([[1]])

    assert not sol.is_feasible
    assert sol.total_tw_violation_sec == 800.0


def test_cmem_emission_model():
    model = CMEMEmissionModel()
    res = model.calculate_emissions(distance_km=20.0, mean_speed_kmh=60.0)

    assert res["co2_grams"] > 0.0
    assert res["fuel_liters"] > 0.0
    # At 60 km/h optimal speed, emissions approx 20 * 140 = 2800g
    assert 2500.0 <= res["co2_grams"] <= 3200.0


def test_bpr_congestion_model():
    bpr = BPRCongestionModel()
    # Free flow = 100s, volume = 500, capacity = 1000
    t_light = bpr.travel_time(free_flow_time=100.0, volume=500.0, capacity=1000.0)
    # Heavy congestion: volume = 2000, capacity = 1000
    t_heavy = bpr.travel_time(free_flow_time=100.0, volume=2000.0, capacity=1000.0)

    assert t_heavy > t_light
