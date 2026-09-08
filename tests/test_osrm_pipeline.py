"""
Tests for OSRM Distance Matrix Pre-computation, O(1) QPSO Fitness Evaluation,
Route Geometry Fetching, and Leaflet Map Road Integration.
"""

from unittest.mock import MagicMock, patch
import pytest

from backend.core.routing.osrm_client import (
    fetch_osrm_distance_matrix,
    fetch_osrm_route_geometry,
    batch_fetch_route_geometries,
    _compute_fallback_matrices,
)
from backend.core.vrp.problem import (
    Customer,
    OptimizationWeights,
    ProblemType,
    Vehicle,
    VRPProblem,
)
from backend.core.vrp.solution import Route, VRPEvaluator, VRPSolution
from backend.core.quantum.qpso import QPSOSolver
from backend.core.graph.network import create_bengaluru_network
from backend.app import build_vrp_problem_from_network


def test_fallback_matrix_computation():
    """Verify fallback distance and duration computation using great-circle + road factor."""
    coords = [(12.9716, 77.5946), (12.9352, 77.6245), (12.9784, 77.6408)]
    time_mat, dist_mat = _compute_fallback_matrices(coords, fallback_speed_kmh=40.0)

    assert len(time_mat) == 3
    assert len(dist_mat) == 3
    for i in range(3):
        assert time_mat[i][i] == 0.0
        assert dist_mat[i][i] == 0.0
        for j in range(3):
            if i != j:
                assert dist_mat[i][j] > 0.0
                assert time_mat[i][j] > 0.0


def test_fetch_osrm_distance_matrix_live_or_fallback():
    """Verify OSRM distance matrix returns proper 2D matrices."""
    # Hub (Majestic) + 2 stops in Bengaluru
    coords = [(12.9716, 77.5946), (12.9352, 77.6245), (12.9784, 77.6408)]
    time_mat, dist_mat = fetch_osrm_distance_matrix(coords, timeout=5.0)

    assert len(time_mat) == 3
    assert len(dist_mat) == 3
    for i in range(3):
        assert time_mat[i][i] == 0.0
        assert dist_mat[i][i] == 0.0
        for j in range(3):
            if i != j:
                assert time_mat[i][j] > 0.0
                assert dist_mat[i][j] > 0.0


def test_qpso_fitness_evaluator_pure_matrix_lookup():
    """
    Ensure the fitness evaluation queries problem.time_matrix and problem.dist_matrix in O(1)
    and does NOT compute Euclidean distances.
    """
    customers = [
        Customer(
            customer_id=1,
            node_id=101,
            name="Customer A",
            lat=12.9352,
            lon=77.6245,
            demand=20.0,
            time_window_start=0.0,
            time_window_end=3600.0,
            service_time=300.0,
        ),
        Customer(
            customer_id=2,
            node_id=102,
            name="Customer B",
            lat=12.9784,
            lon=77.6408,
            demand=30.0,
            time_window_start=0.0,
            time_window_end=3600.0,
            service_time=300.0,
        ),
    ]

    fleet = [Vehicle(vehicle_id=1, capacity=100.0, max_travel_time_sec=14400.0)]

    # Custom synthetic distance and time matrix
    # Index 0: Depot, 1: Cust 1, 2: Cust 2
    time_matrix = [
        [0.0, 500.0, 700.0],
        [500.0, 0.0, 400.0],
        [700.0, 400.0, 0.0],
    ]
    dist_matrix = [
        [0.0, 5.0, 7.0],
        [5.0, 0.0, 4.0],
        [7.0, 4.0, 0.0],
    ]

    problem = VRPProblem(
        problem_id="test_pure_matrix",
        name="Test Pure Matrix Problem",
        problem_type=ProblemType.CVRP,
        depot_node_id=0,
        customers=customers,
        fleet=fleet,
        time_matrix=time_matrix,
        dist_matrix=dist_matrix,
        weights=OptimizationWeights(
            weight_travel_time=1.0,
            weight_distance=1.0,
            weight_emissions=0.0,
            weight_capacity_penalty=100.0,
            weight_time_window_penalty=100.0,
        ),
    )

    evaluator = VRPEvaluator(problem)
    # Route: Depot -> Cust 1 -> Cust 2 -> Depot
    raw_routes = [[1, 2]]
    solution = evaluator.evaluate_routes(raw_routes)

    # Expected distance: dist(0, 1) + dist(1, 2) + dist(2, 0) = 5.0 + 4.0 + 7.0 = 16.0 km
    assert abs(solution.total_distance_km - 16.0) < 1e-4

    # Expected travel time: time(0, 1) + time(1, 2) + time(2, 0) = 500 + 400 + 700 = 1600.0 sec
    assert abs(solution.total_travel_time_sec - 1600.0) < 1e-4

    # Now change matrix value at [1][2] to verify O(1) sensitivity and zero Euclidean dependency
    problem.dist_matrix[1][2] = 25.0
    problem.time_matrix[1][2] = 2000.0
    sol2 = evaluator.evaluate_routes(raw_routes)

    # New distance: 5.0 + 25.0 + 7.0 = 37.0 km
    assert abs(sol2.total_distance_km - 37.0) < 1e-4
    # New travel time: 500 + 2000 + 700 = 3200.0 sec
    assert abs(sol2.total_travel_time_sec - 3200.0) < 1e-4


def test_qpso_solver_with_precomputed_matrix():
    """Verify QPSO optimizer converges properly using the matrix-based cost evaluator."""
    network = create_bengaluru_network()
    problem = build_vrp_problem_from_network(network, num_vehicles=2, vehicle_capacity=80.0)

    # Run QPSO solver
    solver = QPSOSolver(problem, swarm_size=15, max_iterations=20, seed=42)
    solution = solver.solve()

    assert isinstance(solution, VRPSolution)
    assert len(solution.routes) == 2
    assert solution.total_distance_km > 0.0
    assert solution.total_travel_time_sec > 0.0
    assert len(solution.convergence_history) == 20


def test_fetch_osrm_route_geometry():
    """Verify route geometry retrieval returns valid [lat, lon] coordinates."""
    coords = [(12.9716, 77.5946), (12.9352, 77.6245), (12.9716, 77.5946)]
    geometry = fetch_osrm_route_geometry(coords, timeout=5.0)

    assert isinstance(geometry, list)
    assert len(geometry) >= 2
    # Ensure points are formatted as [lat, lon]
    first_pt = geometry[0]
    assert len(first_pt) == 2
    assert 10.0 <= first_pt[0] <= 15.0  # latitude in Bengaluru range
    assert 75.0 <= first_pt[1] <= 80.0  # longitude in Bengaluru range


def test_batch_fetch_route_geometries_enrichment():
    """Verify batch_fetch_route_geometries adds geojson_geometry to route objects and dicts."""
    route = Route(vehicle_id=1, customer_ids=[1, 2])
    depot_coord = (12.9716, 77.5946)
    cust_map = {1: (12.9352, 77.6245), 2: (12.9784, 77.6408)}

    batch_fetch_route_geometries([route], depot_coord, cust_map)

    assert route.geojson_geometry is not None
    assert len(route.geojson_geometry) >= 2
    # Verify serialization includes geojson_geometry
    route_dict = route.stops  # check stops exist
    sol = VRPSolution(routes=[route])
    sol_dict = sol.to_dict()
    assert "geojson_geometry" in sol_dict["routes"][0]
    assert sol_dict["routes"][0]["geojson_geometry"] == route.geojson_geometry


def test_domestic_indian_corridor_strict_enforcement():
    """Verify routing between mainland India and Northeast India strictly sticks to Indian territory."""
    from backend.core.routing.osrm_client import (
        ensure_domestic_indian_waypoints,
        SILIGURI_CORRIDOR,
        GUWAHATI_CORRIDOR,
    )
    from backend.core.graph.india_networks import create_india_national_network

    # Test waypoint expansion for mainland -> Northeast -> Shillong
    kolkata = (22.5726, 88.3639)
    guwahati = (26.1445, 91.7362)
    shillong = (25.5788, 91.8933)

    raw_seq = [kolkata, guwahati, shillong, kolkata]
    expanded = ensure_domestic_indian_waypoints(raw_seq)

    # Siliguri must be in the expanded sequence
    assert any(abs(p[0] - SILIGURI_CORRIDOR[0]) < 0.1 and abs(p[1] - SILIGURI_CORRIDOR[1]) < 0.1 for p in expanded)
    # Guwahati must be in the expanded sequence
    assert any(abs(p[0] - GUWAHATI_CORRIDOR[0]) < 0.1 and abs(p[1] - GUWAHATI_CORRIDOR[1]) < 0.1 for p in expanded)

    # Test graph network topology
    net = create_india_national_network()
    assert len(net.nodes) == 36
    assert net.nodes[34].name.startswith("Siliguri")

    # Shortest path Kolkata (5) to Guwahati (19) must pass through Siliguri (34)
    path, _, _ = net.dijkstra_shortest_path(5, 19)
    assert 34 in path, "Shortest path must transit via Siliguri corridor within Indian territory"
