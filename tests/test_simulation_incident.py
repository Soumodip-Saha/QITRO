import pytest
from backend.core.graph.network import create_bengaluru_network
from backend.core.graph.traffic_models import TrafficIncident
from backend.core.vrp.problem import (
    VRPProblem,
    Customer,
    Vehicle,
    OptimizationWeights,
    ProblemType,
)
from backend.core.quantum.qpso import QPSOSolver
from backend.core.simulation.traffic_simulator import TrafficSimulator


def test_simulation_incident_rerouting():
    network = create_bengaluru_network()
    depot_id = 0
    customers = [
        Customer(
            customer_id=n.node_id,
            node_id=n.node_id,
            name=n.name,
            lat=n.lat,
            lon=n.lon,
            demand=n.demand,
            time_window_start=n.time_window_start,
            time_window_end=n.time_window_end,
            service_time=n.service_time,
        )
        for n in network.nodes.values()
        if not n.is_depot
    ]
    fleet = [Vehicle(vehicle_id=1, capacity=100.0)]
    node_ids = [depot_id] + [c.node_id for c in customers]
    time_mat, dist_mat, paths = network.compute_all_pairs_matrices(node_ids, network.sim_time)

    problem = VRPProblem(
        problem_id="test_prob",
        name="Test Prob",
        problem_type=ProblemType.VRPTW,
        depot_node_id=depot_id,
        customers=customers,
        fleet=fleet,
        time_matrix=time_mat,
        dist_matrix=dist_mat,
        detailed_paths=paths,
        weights=OptimizationWeights(),
        start_time_sec=network.sim_time,
    )

    solver = QPSOSolver(problem, swarm_size=15, max_iterations=30)
    sol = solver.solve()
    assert sol.routes, "Solution should have routes"

    sim = TrafficSimulator(network, problem, sol, time_step_sec=10.0)
    agent = sim.agents[1]
    assert len(agent.current_node_path) >= 2

    # Pick an edge along the planned path
    edge_u = agent.current_node_path[0]
    edge_v = agent.current_node_path[1]

    # Inject incident
    inc = TrafficIncident(
        incident_id="inc_test_1",
        edge_u=edge_u,
        edge_v=edge_v,
        severity=0.95,
        delay_seconds=1200.0,
        start_time=network.sim_time,
        duration_seconds=3600.0,
        description="Major Test Highway Blockage",
    )
    network.add_incident(inc)

    # Step simulation
    state = sim.step()

    # Verify reroute event was recorded
    assert len(sim.reroute_events) > 0, "Reroute event should be recorded"
    assert "Quantum" in sim.reroute_events[0]["message"]
    assert sim.reroute_events[0]["delay_avoided_sec"] > 0
    assert len(state["reroute_events"]) > 0
