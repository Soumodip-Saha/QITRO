"""
FastAPI Server & WebSocket Manager for QITRO:
Quantum-Inspired Intelligent Traffic Route Optimization Platform.
"""

import asyncio
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.core.graph.network import (
    RoadNetwork,
    create_bengaluru_network,
    create_delhi_network,
    create_smart_grid_network,
)
from backend.core.graph.india_networks import (
    create_india_national_network,
    create_north_india_network,
    create_south_india_network,
    create_west_india_network,
    create_east_northeast_network,
    create_mumbai_network,
    create_chennai_network,
    create_hyderabad_network,
    create_kolkata_network,
    create_pune_network,
    create_ahmedabad_network,
)
from backend.core.graph.traffic_models import TrafficIncident, WeatherCondition
from backend.core.vrp.problem import (
    Customer,
    OptimizationWeights,
    ProblemType,
    Vehicle,
    VRPProblem,
)
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
from backend.core.benchmarking.runner import BenchmarkRunner
from backend.core.benchmarking.advanced_analytics import (
    StatisticalHypothesisTester,
    ConvergenceProfiler,
    ScalabilityProfiler,
    QuantumTheoryMetadata,
)
from backend.core.simulation.traffic_simulator import TrafficSimulator


BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="QITRO - Quantum-Inspired Intelligent Traffic Route Optimizer",
    version="1.0.0",
    description="Problem Statement ID: 26137 | Egreen Quanta | Team QBITS",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = BASE_DIR / "frontend" / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# In-memory session state
CURRENT_NETWORK: RoadNetwork = create_bengaluru_network()
CURRENT_PROBLEM: Optional[VRPProblem] = None
CURRENT_SOLUTION: Optional[VRPSolution] = None
CURRENT_SIMULATOR: Optional[TrafficSimulator] = None
LAST_BENCHMARK_REPORT: Optional[Dict[str, Any]] = None


# =====================================================================
# Helper Functions
# =====================================================================

def build_vrp_problem_from_network(
    network: RoadNetwork,
    num_vehicles: int = 3,
    vehicle_capacity: float = 80.0,
    problem_type: ProblemType = ProblemType.VRPTW,
    weights: Optional[OptimizationWeights] = None,
) -> VRPProblem:
    depot_id = next((n.node_id for n in network.nodes.values() if n.is_depot), 0)
    customer_nodes = [n for n in network.nodes.values() if not n.is_depot]

    node_ids = [depot_id] + [n.node_id for n in customer_nodes]
    time_mat, dist_mat, paths = network.compute_all_pairs_matrices(node_ids, network.sim_time)

    customers = []
    for idx, n in enumerate(customer_nodes):
        customers.append(
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
        )

    # Intelligent capacity & travel horizon scaling
    total_demand = sum(c.demand for c in customers)
    net_name_lower = network.name.lower()
    is_national = "national" in net_name_lower or "pan-india" in net_name_lower
    is_regional = "regional" in net_name_lower or "corridor" in net_name_lower

    if is_national:
        eff_cap = max(vehicle_capacity, math.ceil((total_demand / max(1, num_vehicles)) * 1.35), 350.0)
        max_shift = 604800.0  # 7 days
    elif is_regional:
        eff_cap = max(vehicle_capacity, math.ceil((total_demand / max(1, num_vehicles)) * 1.25), 160.0)
        max_shift = 259200.0  # 72 hours regional freight
    else:
        eff_cap = max(vehicle_capacity, math.ceil((total_demand / max(1, num_vehicles)) * 1.15))
        max_shift = 43200.0  # 12 hours intra-city

    fleet = [Vehicle(vehicle_id=v + 1, capacity=eff_cap, max_travel_time_sec=max_shift) for v in range(num_vehicles)]

    problem = VRPProblem(
        problem_id=f"{network.name.lower().replace(' ', '_')}_{len(customers)}c",
        name=f"{network.name} ({len(customers)} Destinations)",
        problem_type=problem_type,
        depot_node_id=depot_id,
        customers=customers,
        fleet=fleet,
        time_matrix=time_mat,
        dist_matrix=dist_mat,
        detailed_paths=paths,
        weights=weights or OptimizationWeights(),
        start_time_sec=network.sim_time,
    )
    return problem


# Initialize default problem
CURRENT_PROBLEM = build_vrp_problem_from_network(CURRENT_NETWORK)


# =====================================================================
# Request / Response Schemas
# =====================================================================

class OptimizeRequest(BaseModel):
    city_id: str = "bengaluru"
    algorithm: str = "QPSO"  # QPSO, QGA, QSA, PSO, GA, SA, GREEDY, CLARKE_WRIGHT
    num_vehicles: int = 3
    vehicle_capacity: float = 80.0
    iterations: int = 120
    swarm_size: int = 35
    weather: str = "clear"
    weight_travel_time: float = 0.40
    weight_distance: float = 0.25
    weight_emissions: float = 0.20


class BenchmarkRequest(BaseModel):
    city_id: str = "bengaluru"
    algorithms: List[str] = ["QPSO", "QGA", "QSA", "PSO", "GA", "SA", "CLARKE_WRIGHT"]
    num_runs: int = 5
    iterations: int = 100
    num_vehicles: int = 3
    vehicle_capacity: float = 80.0


class IncidentRequest(BaseModel):
    edge_u: int
    edge_v: int
    severity: float = 0.8  # 0.0 to 1.0
    delay_seconds: float = 600.0  # 10 min
    duration_seconds: float = 3600.0
    description: str = "Road maintenance blockage"


# =====================================================================
# REST Endpoints
# =====================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = BASE_DIR / "frontend" / "templates" / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>QITRO Frontend Initializing...</h1>", status_code=200)
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "QITRO Optimization Engine",
        "version": "1.0.0",
        "organization": "Egreen Quanta",
        "team": "QBITS",
    }


@app.get("/api/city-presets")
async def get_city_presets():
    preset_file = BASE_DIR / "datasets" / "sample_city_graphs.json"
    if preset_file.exists():
        with open(preset_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cities": []}


NETWORK_FACTORIES = {
    "india_national": create_india_national_network,
    "north_india": create_north_india_network,
    "south_india": create_south_india_network,
    "west_india": create_west_india_network,
    "east_northeast": create_east_northeast_network,
    "mumbai": create_mumbai_network,
    "delhi": create_delhi_network,
    "bengaluru": create_bengaluru_network,
    "chennai": create_chennai_network,
    "hyderabad": create_hyderabad_network,
    "kolkata": create_kolkata_network,
    "pune": create_pune_network,
    "ahmedabad": create_ahmedabad_network,
    "smart_grid": lambda: create_smart_grid_network(5),
}


@app.get("/api/city-graph/{city_id}")
async def get_city_graph(city_id: str):
    global CURRENT_NETWORK, CURRENT_PROBLEM
    if city_id not in NETWORK_FACTORIES:
        raise HTTPException(status_code=404, detail=f"City preset '{city_id}' not found. Available: {list(NETWORK_FACTORIES.keys())}")

    CURRENT_NETWORK = NETWORK_FACTORIES[city_id]()
    CURRENT_PROBLEM = build_vrp_problem_from_network(CURRENT_NETWORK)
    return CURRENT_NETWORK.to_dict()


@app.post("/api/optimize")
async def optimize_route(req: OptimizeRequest):
    global CURRENT_NETWORK, CURRENT_PROBLEM, CURRENT_SOLUTION, CURRENT_SIMULATOR

    # Set weather
    try:
        CURRENT_NETWORK.weather = WeatherCondition(req.weather)
    except ValueError:
        CURRENT_NETWORK.weather = WeatherCondition.CLEAR

    weights = OptimizationWeights(
        weight_travel_time=req.weight_travel_time,
        weight_distance=req.weight_distance,
        weight_emissions=req.weight_emissions,
    )

    CURRENT_PROBLEM = build_vrp_problem_from_network(
        CURRENT_NETWORK,
        num_vehicles=req.num_vehicles,
        vehicle_capacity=req.vehicle_capacity,
        weights=weights,
    )

    runner = BenchmarkRunner(CURRENT_PROBLEM)
    params = {}
    if req.algorithm in ("QPSO", "PSO"):
        params["max_iterations"] = req.iterations
        params["swarm_size"] = req.swarm_size
    elif req.algorithm in ("QGA", "GA"):
        params["max_generations"] = req.iterations
        params["population_size"] = req.swarm_size
    elif req.algorithm in ("QSA", "SA"):
        params["max_iterations"] = req.iterations * 15

    solution = runner.run_single(req.algorithm, params=params)
    CURRENT_SOLUTION = solution

    # Initialize simulator for this solution
    CURRENT_SIMULATOR = TrafficSimulator(CURRENT_NETWORK, CURRENT_PROBLEM, CURRENT_SOLUTION)

    return {
        "solution": solution.to_dict(),
        "problem": CURRENT_PROBLEM.to_dict(),
        "network": CURRENT_NETWORK.to_dict(),
    }


@app.post("/api/benchmark")
async def run_benchmark(req: BenchmarkRequest):
    global CURRENT_NETWORK, CURRENT_PROBLEM, LAST_BENCHMARK_REPORT

    CURRENT_PROBLEM = build_vrp_problem_from_network(
        CURRENT_NETWORK,
        num_vehicles=req.num_vehicles,
        vehicle_capacity=req.vehicle_capacity,
    )

    runner = BenchmarkRunner(CURRENT_PROBLEM)
    report = runner.run_full_benchmark(
        algorithm_keys=req.algorithms,
        num_runs=req.num_runs,
        iterations_override=req.iterations,
    )
    LAST_BENCHMARK_REPORT = report
    return report


@app.post("/api/incident")
async def add_incident(req: IncidentRequest):
    global CURRENT_NETWORK
    incident_id = f"inc_{req.edge_u}_{req.edge_v}_{int(CURRENT_NETWORK.sim_time)}"
    inc = TrafficIncident(
        incident_id=incident_id,
        edge_u=req.edge_u,
        edge_v=req.edge_v,
        severity=req.severity,
        delay_seconds=req.delay_seconds,
        start_time=CURRENT_NETWORK.sim_time,
        duration_seconds=req.duration_seconds,
        description=req.description,
    )
    CURRENT_NETWORK.add_incident(inc)
    return {"message": "Incident added successfully", "incident": inc.__dict__}


@app.delete("/api/incident/{incident_id}")
async def remove_incident(incident_id: str):
    global CURRENT_NETWORK
    CURRENT_NETWORK.remove_incident(incident_id)
    return {"message": f"Incident {incident_id} removed"}


@app.post("/api/simulation/start")
async def start_simulation():
    global CURRENT_SIMULATOR, CURRENT_NETWORK, CURRENT_PROBLEM, CURRENT_SOLUTION
    if CURRENT_SOLUTION is None or CURRENT_PROBLEM is None:
        raise HTTPException(status_code=400, detail="Run optimization first to create routes before simulating.")

    CURRENT_SIMULATOR = TrafficSimulator(CURRENT_NETWORK, CURRENT_PROBLEM, CURRENT_SOLUTION, time_step_sec=15.0)
    return CURRENT_SIMULATOR.get_state()


@app.post("/api/simulation/step")
async def step_simulation():
    global CURRENT_SIMULATOR
    if CURRENT_SIMULATOR is None:
        raise HTTPException(status_code=400, detail="Simulation not started.")

    state = CURRENT_SIMULATOR.step()
    return state


@app.get("/api/export-report")
async def export_report(format: str = "json"):
    global LAST_BENCHMARK_REPORT
    if LAST_BENCHMARK_REPORT is None:
        raise HTTPException(status_code=400, detail="No benchmark report has been generated yet.")

    if format == "csv":
        # Build CSV string
        lines = ["Algorithm,Fitness Mean,Fitness Std,Best Fitness,Distance (km),Travel Time (s),CO2 (kg),Fuel (L),Computation Time (ms),Feasibility Rate (%)"]
        for k, v in LAST_BENCHMARK_REPORT["summaries"].items():
            lines.append(
                f"{v['algorithm_name']},{v['fitness_mean']},{v['fitness_std']},{v['fitness_best']},{v['distance_mean_km']},{v['travel_time_mean_sec']},{v['co2_mean_kg']},{v['fuel_mean_liters']},{v['computation_time_mean_ms']},{v['feasibility_rate_pct']}"
            )
        csv_content = "\n".join(lines)
        return PlainTextResponse(content=csv_content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=qitro_benchmark_report.csv"})

    return JSONResponse(content=LAST_BENCHMARK_REPORT)


# =====================================================================
# Advanced Analytics & Quantum Mechanics Endpoints
# =====================================================================

class ConvergenceProfileRequest(BaseModel):
    algorithm: str = "QPSO"
    num_runs: int = 5
    max_iterations: int = 100


class HypothesisTestRequest(BaseModel):
    quantum_algo: str = "QPSO"
    classical_algo: str = "PSO"
    num_runs: int = 8
    iterations: int = 80


class ScalabilityProfileRequest(BaseModel):
    node_sizes: List[int] = [10, 25, 50, 100, 200]


@app.post("/api/analytics/convergence-profile")
async def get_convergence_profile(req: ConvergenceProfileRequest):
    global CURRENT_PROBLEM
    if CURRENT_PROBLEM is None:
        raise HTTPException(status_code=400, detail="Problem not initialized.")
    profile = ConvergenceProfiler.profile_convergence(
        CURRENT_PROBLEM,
        algorithm_key=req.algorithm,
        num_runs=req.num_runs,
        max_iterations=req.max_iterations,
    )
    return profile


@app.post("/api/analytics/hypothesis-testing")
async def run_hypothesis_testing(req: HypothesisTestRequest):
    global CURRENT_PROBLEM
    if CURRENT_PROBLEM is None:
        raise HTTPException(status_code=400, detail="Problem not initialized.")

    runner = BenchmarkRunner(CURRENT_PROBLEM)
    q_scores = []
    c_scores = []

    for i in range(req.num_runs):
        seed = 200 + i * 31
        q_sol = runner.run_single(req.quantum_algo, params={"max_iterations": req.iterations}, seed=seed)
        c_sol = runner.run_single(req.classical_algo, params={"max_iterations": req.iterations}, seed=seed)
        q_scores.append(q_sol.fitness_score)
        c_scores.append(c_sol.fitness_score)

    test_res = StatisticalHypothesisTester.run_paired_tests(q_scores, c_scores)
    test_res["quantum_algorithm"] = req.quantum_algo
    test_res["classical_algorithm"] = req.classical_algo
    test_res["quantum_raw_scores"] = [round(s, 2) for s in q_scores]
    test_res["classical_raw_scores"] = [round(s, 2) for s in c_scores]
    return test_res


@app.post("/api/analytics/scalability-profile")
async def get_scalability_profile(req: ScalabilityProfileRequest):
    profile = ScalabilityProfiler.profile_scalability(req.node_sizes)
    return profile


@app.get("/api/theory/quantum-math")
async def get_quantum_theory_metadata():
    return QuantumTheoryMetadata.get_mathematical_foundations()


# =====================================================================
# WebSocket Endpoint for Live Streaming
# =====================================================================

@app.websocket("/ws/live-stream")
async def websocket_live_stream(websocket: WebSocket):
    await websocket.accept()
    global CURRENT_NETWORK, CURRENT_PROBLEM, CURRENT_SIMULATOR

    try:
        while True:
            data_raw = await websocket.receive_text()
            data = json.loads(data_raw)
            action = data.get("action")

            if action == "run_live_optimization":
                algo = data.get("algorithm", "QPSO")
                iterations = data.get("iterations", 100)
                swarm_size = data.get("swarm_size", 30)

                runner = BenchmarkRunner(CURRENT_PROBLEM)
                params = {"max_iterations": iterations, "swarm_size": swarm_size}

                def ws_progress(step_data):
                    # Synchronous callback pushed via event loop
                    asyncio.create_task(
                        websocket.send_json({"type": "optimization_progress", "data": step_data})
                    )

                solution = runner.run_single(algo, params=params, progress_callback=ws_progress)
                await websocket.send_json(
                    {
                        "type": "optimization_completed",
                        "solution": solution.to_dict(),
                    }
                )

            elif action == "sim_step":
                if CURRENT_SIMULATOR:
                    state = CURRENT_SIMULATOR.step()
                    await websocket.send_json({"type": "simulation_state", "data": state})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close()
