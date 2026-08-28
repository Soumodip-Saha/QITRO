# Quantum-Inspired Intelligent Traffic Route Optimization (QITRO)

**Problem Statement ID:** 26137  
**Title:** Quantum-Inspired Intelligent Traffic Route Optimization in Transportation Systems Using Metaheuristic Optimization  
**Organization / Department:** Egreen Quanta  
**Team:** QBITS  
**Category:** Software | **Theme:** Transportation & Logistics  

---

## 1. Executive Summary

Urban traffic congestion, delivery delays, and mounting carbon emissions represent critical bottlenecks in modern smart-city logistics and Intelligent Transportation Systems (ITS). Classical exact methods (e.g., Integer Linear Programming) fail to scale for NP-hard Vehicle Routing Problems (VRP), while standard metaheuristics often suffer from premature convergence into local minima.

**QITRO** is an enterprise-grade optimization and simulation platform that implements **Quantum-Inspired Metaheuristic Algorithms** (principally Quantum-behaved Particle Swarm Optimization - QPSO, Quantum Genetic Algorithms - QGA, and Quantum Simulated Annealing - QSA). These algorithms embed quantum-mechanical principles—such as wave functions in $\delta$-potential wells, probability amplitudes, quantum rotation gates, and quantum tunneling—into classical computational architectures to achieve superior global exploration, accelerated convergence, and dynamic real-time traffic adaptation.

---

## 2. Delivery Table (Expected Deliverables)

| Deliverable ID | Deliverable Name | Description & Technical Scope | Key Features & Output Artifacts | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DEL-01** | **Mathematical Optimization Formulation** | Multi-objective formulation for dynamic urban routing, Capacitated VRP (CVRP), and VRP with Time Windows (VRPTW). | Mathematical specification of cost function: travel time $T(t)$, travel distance $D$, congestion delay $\Gamma(t)$, carbon emissions $E(t)$, and penalty functions. | **COMPLETE** |
| **DEL-02** | **Quantum-Inspired Metaheuristic Engine** | Implementation of quantum metaheuristics incorporating quantum mechanics principles. | • **QPSO Engine**: Delta potential well, Mean Best Position ($mbest$), adaptive contraction-expansion coefficient ($\alpha$), Ranked Order Value (ROV) permutation decoding.<br>• **QGA Engine**: Q-bit representation ($[\alpha, \beta]^T$), quantum rotation gates, dynamic phase shifting, Pauli-X mutation.<br>• **QSA Engine**: Transverse-field quantum tunneling barrier penetration. | **COMPLETE** |
| **DEL-03** | **Classical Metaheuristic & Exact Baselines** | Standard benchmark algorithms for comparative evaluation. | • Standard Particle Swarm Optimization (PSO)<br>• Classical Genetic Algorithm (GA)<br>• Classical Simulated Annealing (SA)<br>• Clarke-Wright Savings & Greedy Nearest Neighbor baselines. | **COMPLETE** |
| **DEL-04** | **Dynamic Network & Traffic Modeling** | Graph-based transportation model supporting realistic city road networks and synthetic smart-city grids. | • Node/Edge graph with road classifications, capacities, speed limits.<br>• Dynamic congestion factor (BPR function / time-dependent traffic waves).<br>• Real-time incident injection (accidents, road blockades, weather delays, dynamic detour re-triggering). | **COMPLETE** |
| **DEL-05** | **Benchmarking & Convergence Analytics Suite** | Automated evaluation engine measuring statistical, operational, and green logistics KPIs. | • Hypervolume, Pareto optimality, convergence curves (Fitness vs Iteration).<br>• Execution latency, travel time reduction (%), fuel/CO2 emissions reduction (g CO2/km).<br>• Statistical significance tests (Wilcoxon signed-rank test, standard deviation, boxplots). | **COMPLETE** |
| **DEL-06** | **Interactive Web Simulation Platform & UI** | Full-stack interactive visual dashboard for live traffic simulation, algorithm control, and quantum state inspection. | • **Interactive City Map**: Leaflet/MapLibre map with moving vehicle agents, congestion heatmaps, and route overlays.<br>• **Quantum Visualizer**: Bloch sphere / Q-bit probability distributions and wave function collapse dynamics.<br>• **Benchmark Arena**: Side-by-side live execution comparison.<br>• **Scenario Builder**: Custom fleet, customer demand, time window, and incident creator. | **COMPLETE** |
| **DEL-07** | **Documentation, API Specs & Test Suite** | Production-ready documentation, REST/WebSocket API endpoints, and automated test coverage. | • OpenAPI/Swagger specification.<br>• Unit & integration test suite (`pytest`).<br>• Comprehensive User Guide & Architecture Technical Whitepaper. | **COMPLETE** |

---

## 3. Mathematical Foundations

### 3.1 Dynamic Travel Time (BPR Congestion Function)
The link travel time $T_{ij}(t)$ on edge $(i, j)$ at departure time $t$ is formulated via the Bureau of Public Roads (BPR) equation:
$$T_{ij}(t) = \frac{d_{ij}}{v_{ij}^{\max}} \cdot \left[ 1 + \alpha_{BPR} \left(\frac{V_{ij}(t)}{C_{ij}}\right)^{\beta_{BPR}} \right] + \delta_{ij}(t)$$
where:
- $d_{ij}$ is segment distance in km,
- $v_{ij}^{\max}$ is speed limit in km/h,
- $V_{ij}(t)$ is live vehicle flow volume,
- $C_{ij}$ is link capacity in vehicles/hour,
- $\alpha_{BPR} = 0.15, \beta_{BPR} = 4.0$,
- $\delta_{ij}(t)$ is stochastic incident delay.

### 3.2 Vehicle Emissions & Fuel Consumption (CMEM Model)
Carbon emissions are calculated via the Comprehensive Modal Emission Model (CMEM):
$$E_{ij}(t) = d_{ij} \cdot \left( k_0 + k_1 \cdot \bar{v}_{ij}(t) + k_2 \cdot \bar{v}_{ij}(t)^2 \right)$$

### 3.3 Multi-Objective Cost Function
$$\min \mathcal{F}(\mathbf{R}) = w_1 \sum_{k=1}^K T(\text{Route}_k) + w_2 \sum_{k=1}^K D(\text{Route}_k) + w_3 \sum_{k=1}^K E(\text{Route}_k) + \sum_{p} \lambda_p \cdot \text{Penalty}_p$$

---

## 4. Quantum-Inspired Algorithms

### 4.1 Quantum-behaved Particle Swarm Optimization (QPSO)
In QPSO, a particle's state is described by a wave function $\psi(x)$ in a $\delta$-potential well centered at the local attractor $p_{i,j}$:
$$p_{i,j}(t) = \phi \cdot P_{i,j}(t) + (1-\phi) \cdot G_j(t), \quad \phi \sim U(0, 1)$$
The Mean Best Position ($mbest$) is computed across the swarm of size $M$:
$$mbest(t) = \frac{1}{M} \sum_{i=1}^M P_i(t)$$
The position update follows Monte Carlo sampling of the collapsed wave function:
$$x_{i,j}(t+1) = p_{i,j}(t) \pm \alpha(t) \cdot \left| mbest_j(t) - x_{i,j}(t) \right| \cdot \ln\left(\frac{1}{u}\right), \quad u \sim U(0, 1)$$
with adaptive contraction-expansion coefficient $\alpha(t) = \alpha_{\max} - \frac{\alpha_{\max} - \alpha_{\min}}{T_{\max}} \cdot t$.
Continuous positions are transformed into valid customer permutations via **Ranked Order Value (ROV)** decoding.

### 4.2 Quantum Genetic Algorithm (QGA)
Chromosomes are formulated as vectors of Q-bits:
$$q_j = \begin{bmatrix} \alpha_j \\ \beta_j \end{bmatrix}, \quad |\alpha_j|^2 + |\beta_j|^2 = 1$$
States are updated via Quantum Rotation Gates:
$$\begin{bmatrix} \alpha_j^{t+1} \\ \beta_j^{t+1} \end{bmatrix} = \begin{bmatrix} \cos(\Delta \theta_j) & -\sin(\Delta \theta_j) \\ \sin(\Delta \theta_j) & \cos(\Delta \theta_j) \end{bmatrix} \begin{bmatrix} \alpha_j^t \\ \beta_j^t \end{bmatrix}$$
Rotation angle $\Delta \theta_j$ is adaptively determined from a lookup table comparing individual states against the current global best solution.

### 4.3 Quantum Simulated Annealing (QSA)
Simulates quantum tunneling through tall potential barriers by incorporating a transverse quantum fluctuation field $\Gamma(t) = \Gamma_0 (1 - t/T_{\max})^{1.5}$ alongside thermal cooling $T(t) = T_0 \cdot \gamma^t$:
$$P_{\text{accept}}(\Delta E, \Gamma, T) = \min\left(1, \exp\left(-\frac{\Delta E}{k_B T}\right) + \tanh\left(\frac{\Gamma}{T + \epsilon}\right)\right)$$

---

## 5. System Architecture

```
d:\QITRO\
├── backend/
│   ├── app.py                          # FastAPI server + WebSocket streaming
│   ├── core/
│   │   ├── graph/
│   │   │   ├── network.py              # Road network graph, Dijkstra, City maps
│   │   │   └── traffic_models.py       # BPR congestion, CMEM emissions, incidents
│   │   ├── vrp/
│   │   │   ├── problem.py              # CVRP, VRPTW, DVRP problem formulation
│   │   │   └── solution.py             # Route evaluator, penalties, emissions
│   │   ├── quantum/
│   │   │   ├── qpso.py                 # QPSO solver with delta well & ROV
│   │   │   ├── qga.py                  # QGA with Q-bits & rotation gates
│   │   │   └── qsa.py                  # QSA with quantum tunneling
│   │   ├── classical/
│   │   │   ├── pso.py                  # Classical PSO baseline
│   │   │   ├── ga.py                   # Classical GA baseline (OX crossover)
│   │   │   ├── sa.py                   # Classical Simulated Annealing
│   │   │   └── baselines.py            # Clarke-Wright & Nearest Neighbor
│   │   ├── benchmarking/
│   │   │   ├── runner.py               # Multi-run comparative benchmark executor
│   │   │   └── statistics.py           # Wilcoxon test, boxplots, metrics
│   │   └── simulation/
│   │       └── traffic_simulator.py    # Microscopic agent traffic simulation & dynamic reroute
├── frontend/
│   ├── static/
│   │   ├── css/styles.css              # Dark-mode quantum UI stylesheet
│   │   └── js/
│   │       ├── api.js                  # REST & WebSocket client
│   │       ├── map_view.js             # Leaflet live route & agent renderer
│   │       ├── quantum_view.js         # Canvas wave-function & delta-well inspector
│   │       ├── benchmark_view.js       # Chart.js convergence plots & stats table
│   │       └── app.js                  # Main controller & incident triggers
│   └── templates/
│       └── index.html                  # Single-page dashboard application
├── tests/                              # Pytest test suite (100% pass)
├── datasets/                           # City network presets & VRP benchmarks
├── requirements.txt
└── README.md
```

---

## 6. Installation & Execution

### Prerequisites
- Python 3.10+

### Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run automated test suite
pytest tests/ -v

# 3. Launch the platform server
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

### Accessing the Web Dashboard
Open your browser and navigate to:
```
http://127.0.0.1:8000
```
- **Run Optimization**: Select a city (Bengaluru, Delhi, Smart Grid), pick an algorithm (QPSO, QGA, QSA, PSO, GA, SA), and view optimal multi-vehicle routes on the interactive map.
- **Full Benchmark Arena**: Run side-by-side multi-seed statistical benchmarking with live convergence plots and Wilcoxon significance $p$-values.
- **Simulate Dynamic Traffic**: Press **Play Sim** to watch vehicles navigate their routes in real time.
- **Inject Incidents**: Click **Inject Incident** to simulate sudden road blockages, and observe automatic quantum rerouting in real time.
- **Export Data**: Download JSON or CSV benchmark reports.
