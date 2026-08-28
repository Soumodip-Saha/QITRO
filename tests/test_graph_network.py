"""
Unit Tests for Pan-India Road Networks, Regional Corridors, and Metropolitan Grids
"""

from backend.core.graph.network import (
    RoadNetwork,
    Node,
    Edge,
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


def test_india_national_network_generation():
    net = create_india_national_network()
    assert len(net.nodes) == 36
    assert len(net.edges) >= 30
    assert net.nodes[0].is_depot
    assert "Nagpur" in net.nodes[0].name

    # Verify long-distance connectivity (Delhi to Chennai via NH48 / NH44)
    path, travel_time, dist = net.dijkstra_shortest_path(1, 4)
    assert len(path) >= 3
    assert path[0] == 1
    assert path[-1] == 4
    assert dist > 1500.0


def test_regional_networks():
    north = create_north_india_network()
    assert len(north.nodes) == 12
    assert north.nodes[0].is_depot

    south = create_south_india_network()
    assert len(south.nodes) == 12
    assert south.nodes[0].is_depot

    west = create_west_india_network()
    assert len(west.nodes) == 12
    assert west.nodes[0].is_depot

    east_ne = create_east_northeast_network()
    assert len(east_ne.nodes) == 12
    assert east_ne.nodes[0].is_depot


def test_metro_networks():
    mumbai = create_mumbai_network()
    assert len(mumbai.nodes) == 12
    assert mumbai.nodes[0].is_depot

    chennai = create_chennai_network()
    assert len(chennai.nodes) == 12
    assert chennai.nodes[0].is_depot

    hyderabad = create_hyderabad_network()
    assert len(hyderabad.nodes) == 12
    assert hyderabad.nodes[0].is_depot

    kolkata = create_kolkata_network()
    assert len(kolkata.nodes) == 12
    assert kolkata.nodes[0].is_depot

    pune = create_pune_network()
    assert len(pune.nodes) == 12
    assert pune.nodes[0].is_depot

    ahmedabad = create_ahmedabad_network()
    assert len(ahmedabad.nodes) == 12
    assert ahmedabad.nodes[0].is_depot


def test_bengaluru_network_generation():
    net = create_bengaluru_network()
    assert len(net.nodes) == 16
    assert len(net.edges) > 0
    assert net.nodes[0].is_depot


def test_delhi_network_generation():
    net = create_delhi_network()
    assert len(net.nodes) == 12
    assert net.nodes[0].is_depot


def test_smart_grid_generation():
    net = create_smart_grid_network(4)
    assert len(net.nodes) == 16


def test_dijkstra_shortest_path():
    net = create_bengaluru_network()
    path, travel_time, dist = net.dijkstra_shortest_path(0, 3)  # Majestic to Whitefield

    assert len(path) >= 2
    assert path[0] == 0
    assert path[-1] == 3
    assert travel_time > 0.0
    assert dist > 0.0


def test_incident_injection_and_delay():
    net = create_bengaluru_network()
    _, orig_time, _ = net.dijkstra_shortest_path(0, 6, departure_time=28800.0)

    inc = TrafficIncident(
        incident_id="inc_0_6",
        edge_u=0,
        edge_v=6,
        severity=1.0,
        delay_seconds=1200.0,
        start_time=28000.0,
        duration_seconds=3600.0,
    )
    net.add_incident(inc)

    _, delayed_time, _ = net.dijkstra_shortest_path(0, 6, departure_time=28800.0)
    assert delayed_time > orig_time

    net.remove_incident("inc_0_6")
    _, restored_time, _ = net.dijkstra_shortest_path(0, 6, departure_time=28800.0)
    assert abs(restored_time - orig_time) < 1e-4
