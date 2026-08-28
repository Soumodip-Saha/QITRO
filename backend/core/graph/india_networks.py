"""
Pan-India Road Networks & City Topologies:
- All-India National Highway Logistics Network (36 Major Hubs across all States)
- Regional Logistics Zones (North, South, West, East & Northeast India)
- Dedicated Metropolitan Urban Networks (Mumbai, Chennai, Hyderabad, Kolkata, Pune, Ahmedabad)
"""

import math
from typing import List, Tuple
from backend.core.graph.network import Node, Edge, RoadNetwork, haversine_distance_km


def create_india_national_network() -> RoadNetwork:
    """
    Pan-India National Highway Logistics Network:
    Golden Quadrilateral, North-South Corridor (NH44), East-West Corridor (NH27),
    Coastal Highway (NH66), and Major Industrial Freight Hubs.
    """
    net = RoadNetwork("Pan-India National Logistics Highway Network (36 Major Hubs)")

    # 36 Major Indian Cities / Freight Logistics Hubs
    # (id, name, lat, lon, is_depot, demand, tw_start, tw_end)
    cities = [
        # Central Hub (Zero Mile)
        (0, "Nagpur Central Logistics Hub (Zero Mile)", 21.1458, 79.0882, True, 0.0, 0, 86400),
        # Metros & Capitals
        (1, "New Delhi (National Capital Freight Center)", 28.6139, 77.2090, False, 45.0, 25200, 43200),
        (2, "Mumbai (JNPT & Western Maritime Hub)", 19.0760, 72.8777, False, 50.0, 27000, 45000),
        (3, "Bengaluru (Southern Tech & Logistics Hub)", 12.9716, 77.5946, False, 45.0, 27000, 45000),
        (4, "Chennai (Automotive & Port Corridor)", 13.0827, 80.2707, False, 40.0, 28800, 46800),
        (5, "Kolkata (Eastern Riverine & Trade Gateway)", 22.5726, 88.3639, False, 42.0, 27000, 45000),
        (6, "Hyderabad (Deccan Pharma & IT Hub)", 17.3850, 78.4867, False, 38.0, 28800, 46800),
        (7, "Ahmedabad (Gujarat Industrial Express Hub)", 23.0225, 72.5714, False, 35.0, 27000, 43200),
        (8, "Pune (Auto & Engineering Corridor)", 18.5204, 73.8567, False, 32.0, 28800, 45000),
        (9, "Jaipur (Pink City North-West Hub)", 26.9124, 75.7873, False, 25.0, 28800, 43200),
        (10, "Lucknow (Awadh Regional Freight Hub)", 26.8467, 80.9462, False, 28.0, 27000, 43200),
        (11, "Chandigarh (Northern Tricity Terminal)", 30.7333, 76.7794, False, 24.0, 28800, 41400),
        (12, "Kochi (Cochin Deep Sea Port Hub)", 9.9312, 76.2673, False, 30.0, 30600, 48600),
        (13, "Visakhapatnam (Vizag Maritime Port)", 17.6868, 83.2185, False, 32.0, 28800, 46800),
        (14, "Surat (Textile & Diamond Express Hub)", 21.1702, 72.8311, False, 28.0, 27000, 43200),
        (15, "Bhopal (Central MP Industrial Center)", 23.2599, 77.4126, False, 22.0, 28800, 43200),
        (16, "Indore (Commercial Logistics Capital of MP)", 22.7196, 75.8577, False, 26.0, 28800, 43200),
        (17, "Patna (Bihar Central Trade Hub)", 25.5941, 85.1376, False, 30.0, 28800, 45000),
        (18, "Bhubaneswar (Odisha Mining & IT Hub)", 20.2961, 85.8245, False, 28.0, 28800, 45000),
        (19, "Guwahati (Northeast Gateway Corridor)", 26.1445, 91.7362, False, 35.0, 32400, 50400),
        (20, "Varanasi (Purvanchal Freight Center)", 25.3176, 82.9739, False, 22.0, 28800, 43200),
        (21, "Agra (Expressway Interchange Hub)", 27.1767, 78.0081, False, 20.0, 27000, 41400),
        (22, "Kanpur (Leather & Defense Industrial Hub)", 26.4499, 80.3319, False, 26.0, 27000, 43200),
        (23, "Amritsar (Grand Trunk Frontier Hub)", 31.6340, 74.8723, False, 20.0, 30600, 45000),
        (24, "Dehradun (Himalayan Foothills Terminal)", 30.3165, 78.0322, False, 18.0, 30600, 45000),
        (25, "Srinagar (NH44 Northern Origin)", 34.0837, 74.7973, False, 20.0, 32400, 50400),
        (26, "Panaji (Goa Coastal Maritime Port)", 15.4909, 73.8278, False, 18.0, 30600, 46800),
        (27, "Coimbatore (Pump & Textile Capital)", 11.0168, 76.9558, False, 24.0, 28800, 45000),
        (28, "Madurai (Southern TN Distribution Node)", 9.9252, 78.1198, False, 22.0, 30600, 46800),
        (29, "Vijayawada (AP Central Riverine Terminal)", 16.5062, 80.6480, False, 25.0, 28800, 45000),
        (30, "Raipur (Chhattisgarh Steel Freight Hub)", 21.2514, 81.6296, False, 26.0, 28800, 45000),
        (31, "Ranchi (Jharkhand Mineral Core)", 23.3441, 85.3096, False, 24.0, 28800, 45000),
        (32, "Jamshedpur (Tata Heavy Industry Hub)", 22.8046, 86.2029, False, 26.0, 28800, 45000),
        (33, "Mangaluru (New Mangalore Port SEZ)", 12.9141, 74.8560, False, 22.0, 30600, 46800),
        (34, "Vadodara (Gujarat Petrochemical Hub)", 22.3072, 73.1812, False, 24.0, 27000, 43200),
        (35, "Shillong (Meghalaya Hill Terminal)", 25.5788, 91.8933, False, 15.0, 34200, 52200),
    ]

    for c in cities:
        net.add_node(
            Node(
                node_id=c[0],
                name=c[1],
                lat=c[2],
                lon=c[3],
                is_depot=c[4],
                demand=c[5],
                time_window_start=float(c[6]),
                time_window_end=float(c[7]),
            )
        )

    # National Highway Arterials
    # Format: (u, v, highway_name, speed_limit_kmh, capacity_vph, volume)
    highways = [
        # Golden Quadrilateral & NH48 (Delhi - Jaipur - Ahmedabad - Mumbai - Pune - Bangalore - Chennai)
        (1, 9, "NH48 (Delhi-Jaipur Expressway)", 90, 3200, 2200),
        (9, 7, "NH48 (Jaipur-Ahmedabad Corridor)", 85, 2800, 1800),
        (7, 34, "NE1 (Ahmedabad-Vadodara Expressway)", 100, 3500, 2400),
        (34, 14, "NH48 (Vadodara-Surat Highway)", 90, 3200, 2300),
        (14, 2, "NH48 (Surat-Mumbai Western Corridor)", 85, 3600, 2700),
        (2, 8, "Mumbai-Pune Expressway", 100, 3800, 2900),
        (8, 3, "NH48 (Pune-Bengaluru Highway via Kolhapur/Belagavi)", 85, 2900, 1900),
        (3, 4, "Bangalore-Chennai Expressway / NH48", 95, 3400, 2400),

        # NH16 (Chennai - Vijayawada - Visakhapatnam - Bhubaneswar - Kolkata)
        (4, 29, "NH16 (Chennai-Vijayawada Coastal)", 85, 2800, 1800),
        (29, 13, "NH16 (Vijayawada-Visakhapatnam)", 85, 2700, 1700),
        (13, 18, "NH16 (Visakhapatnam-Bhubaneswar)", 85, 2600, 1600),
        (18, 5, "NH16 (Bhubaneswar-Kolkata Eastern Quadrilateral)", 85, 3000, 2100),

        # NH19 (Delhi - Agra - Kanpur - Varanasi - Kolkata)
        (1, 21, "Yamuna Expressway (Delhi-Agra)", 100, 3600, 2300),
        (21, 22, "Agra-Lucknow Expressway link to Kanpur", 95, 3400, 2100),
        (22, 20, "NH19 (Kanpur-Varanasi Grand Trunk)", 85, 2800, 1900),
        (20, 5, "NH19 (Varanasi-Kolkata Eastern Trunk)", 85, 2900, 2000),

        # North-South Corridor NH44 (Srinagar - Amritsar - Delhi - Agra - Gwalior - Nagpur - Hyderabad - Bangalore - Madurai)
        (25, 23, "NH44 (Srinagar-Amritsar Jammu Corridor)", 70, 1800, 1100),
        (23, 11, "NH44 (Amritsar-Chandigarh GT Road)", 85, 2600, 1700),
        (11, 1, "NH44 (Chandigarh-Delhi Highway)", 90, 3400, 2500),
        (1, 24, "Delhi-Dehradun Expressway", 80, 2400, 1600),
        (21, 15, "NH44/NH46 (Agra-Gwalior-Bhopal)", 80, 2200, 1400),
        (15, 0, "NH46/NH44 (Bhopal-Nagpur Central Link)", 85, 2600, 1600),
        (0, 6, "NH44 (Nagpur-Hyderabad North-South Spine)", 90, 3000, 2000),
        (6, 3, "NH44 (Hyderabad-Bengaluru Express Corridor)", 90, 3200, 2200),
        (3, 27, "NH544 (Bengaluru-Coimbatore-Salem)", 85, 2800, 1900),
        (27, 12, "NH544 (Coimbatore-Kochi Corridor)", 80, 2600, 1800),
        (27, 28, "NH83 (Coimbatore-Madurai)", 80, 2200, 1400),
        (4, 28, "NH38 (Chennai-Madurai Central TN)", 85, 2600, 1700),

        # Central Cross Corridors (Nagpur to West, East, and Central)
        (0, 2, "Samruddhi Mahamarg (Nagpur-Mumbai Super Expressway)", 110, 4000, 2500),
        (0, 8, "Nagpur-Pune Industrial Highway", 80, 2400, 1600),
        (0, 16, "NH47 (Nagpur-Indore)", 80, 2200, 1400),
        (16, 7, "Indore-Ahmedabad Highway (NH47)", 85, 2600, 1700),
        (16, 15, "Indore-Bhopal State Expressway", 90, 2800, 1800),
        (0, 30, "NH53 (Nagpur-Raipur Steel Corridor)", 85, 2600, 1700),
        (30, 18, "NH53 (Raipur-Sambalpur-Bhubaneswar)", 80, 2200, 1400),
        (30, 31, "NH43 (Raipur-Ranchi)", 75, 1900, 1200),

        # East-West Corridors & Northeast Gateway (NH27)
        (10, 1, "Lucknow-Delhi Expressway link", 95, 3200, 2100),
        (10, 22, "Lucknow-Kanpur Expressway", 90, 3400, 2500),
        (10, 20, "Purvanchal Expressway (Lucknow-Varanasi)", 100, 3500, 2100),
        (20, 17, "NH19/NH922 (Varanasi-Patna)", 80, 2400, 1600),
        (17, 31, "NH22 (Patna-Ranchi)", 75, 2000, 1300),
        (31, 32, "NH18 (Ranchi-Jamshedpur)", 80, 2200, 1500),
        (32, 5, "NH16/NH18 (Jamshedpur-Kolkata)", 85, 2600, 1800),
        (17, 19, "NH27 (Patna-Siliguri-Guwahati East-West Corridor)", 80, 2400, 1600),
        (5, 19, "Kolkata-Siliguri-Guwahati Highway", 80, 2500, 1700),
        (19, 35, "Guwahati-Shillong Expressway (NH6)", 70, 1800, 1200),

        # Coastal Highway (NH66) & Deccan Links
        (2, 26, "NH66 (Mumbai-Goa Coastal Highway)", 75, 2200, 1500),
        (26, 33, "NH66 (Goa-Mangaluru Coastal Highway)", 80, 2300, 1500),
        (33, 12, "NH66 (Mangaluru-Kochi Coastal)", 80, 2400, 1600),
        (3, 33, "NH75 (Bengaluru-Hassan-Mangaluru)", 75, 2200, 1500),
        (6, 29, "NH65 (Hyderabad-Vijayawada)", 85, 2800, 1900),
        (6, 13, "Hyderabad-Visakhapatnam Express Highway", 85, 2600, 1700),
        (8, 26, "Pune-Kolhapur-Goa link", 80, 2400, 1600),
    ]

    for u, v, hwy_name, spd, cap, vol in highways:
        n1 = net.nodes[u]
        n2 = net.nodes[v]
        # Realistic highway road distance factor (approx 1.18x haversine)
        dist = round(haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon) * 1.18, 1)
        net.add_edge(
            Edge(
                u=u,
                v=v,
                distance_km=max(15.0, dist),
                speed_limit_kmh=spd,
                capacity_vph=cap,
                current_volume=vol,
                road_type="highway",
            ),
            bidirectional=True,
        )

    return net


def create_north_india_network() -> RoadNetwork:
    """North India Regional Logistics Corridor."""
    net = RoadNetwork("North India Regional Logistics Corridor")
    cities = [
        (0, "Delhi NCR Central Gateway (Depot)", 28.6139, 77.2090, True, 0.0, 0, 86400),
        (1, "Gurugram Cyber & Auto Hub", 28.4595, 77.0266, False, 28.0, 27000, 36000),
        (2, "Noida Electronic City & Tech Park", 28.5355, 77.3910, False, 30.0, 28800, 37800),
        (3, "Chandigarh IT & Logistics Tricity", 30.7333, 76.7794, False, 26.0, 28800, 39600),
        (4, "Jaipur Sitapura Industrial Area", 26.9124, 75.7873, False, 32.0, 28800, 41400),
        (5, "Agra Transport Nagar Hub", 27.1767, 78.0081, False, 22.0, 28800, 39600),
        (6, "Lucknow Transport Nagar", 26.8467, 80.9462, False, 35.0, 30600, 43200),
        (7, "Kanpur Panki Industrial Estate", 26.4499, 80.3319, False, 30.0, 30600, 43200),
        (8, "Amritsar GT Road Terminal", 31.6340, 74.8723, False, 24.0, 32400, 45000),
        (9, "Dehradun Selaqui Pharma Hub", 30.3165, 78.0322, False, 20.0, 30600, 43200),
        (10, "Varanasi Shivpur Logistics Node", 25.3176, 82.9739, False, 25.0, 32400, 46800),
        (11, "Ludhiana Textile & Cycle Hub", 30.9010, 75.8573, False, 28.0, 30600, 43200),
    ]

    for c in cities:
        net.add_node(Node(c[0], c[2], c[3], c[1], c[4], c[5], float(c[6]), float(c[7])))

    conns = [
        (0, 1, 90, 3200, 2200),
        (0, 2, 85, 3000, 2100),
        (0, 3, 90, 3400, 2400),
        (3, 11, 85, 2800, 1900),
        (11, 8, 85, 2800, 1800),
        (0, 4, 90, 3200, 2200),
        (0, 5, 100, 3600, 2300),
        (5, 6, 95, 3400, 2100),
        (6, 7, 90, 3400, 2500),
        (6, 10, 100, 3500, 2100),
        (0, 9, 80, 2400, 1600),
        (3, 9, 75, 2000, 1300),
    ]

    for u, v, spd, cap, vol in conns:
        n1, n2 = net.nodes[u], net.nodes[v]
        dist = round(haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon) * 1.15, 1)
        net.add_edge(Edge(u, v, max(10.0, dist), spd, cap, vol, road_type="highway"), bidirectional=True)

    return net


def create_south_india_network() -> RoadNetwork:
    """South India Regional Logistics Corridor."""
    net = RoadNetwork("South India Regional Logistics Corridor")
    cities = [
        (0, "Bengaluru Central Freight Hub (Depot)", 12.9716, 77.5946, True, 0.0, 0, 86400),
        (1, "Chennai Port & Auto SEZ", 13.0827, 80.2707, False, 40.0, 27000, 43200),
        (2, "Hyderabad Cyberabad & Pharma Hub", 17.3850, 78.4867, False, 38.0, 27000, 43200),
        (3, "Kochi Port & Vallarpadam ICTT", 9.9312, 76.2673, False, 32.0, 30600, 46800),
        (4, "Coimbatore Engineering SEZ", 11.0168, 76.9558, False, 26.0, 28800, 43200),
        (5, "Madurai South TN Logistics Hub", 9.9252, 78.1198, False, 24.0, 30600, 45000),
        (6, "Visakhapatnam Port City", 17.6868, 83.2185, False, 30.0, 32400, 48600),
        (7, "Vijayawada Auto Nagar Hub", 16.5062, 80.6480, False, 28.0, 28800, 45000),
        (8, "Mysuru Hebbal Industrial Area", 12.2958, 76.6394, False, 18.0, 27000, 37800),
        (9, "Mangaluru NMPT Gateway", 12.9141, 74.8560, False, 22.0, 30600, 45000),
        (10, "Kozhikode Malabar Trade Center", 11.2588, 75.7804, False, 20.0, 30600, 45000),
        (11, "Thiruvananthapuram Technopark", 8.5241, 76.9366, False, 22.0, 32400, 48600),
    ]

    for c in cities:
        net.add_node(Node(c[0], c[2], c[3], c[1], c[4], c[5], float(c[6]), float(c[7])))

    conns = [
        (0, 1, 95, 3400, 2400),
        (0, 2, 90, 3200, 2200),
        (0, 8, 90, 3000, 2000),
        (0, 9, 75, 2200, 1500),
        (0, 4, 85, 2800, 1900),
        (4, 3, 80, 2600, 1800),
        (4, 5, 80, 2200, 1400),
        (1, 5, 85, 2600, 1700),
        (1, 7, 85, 2800, 1800),
        (7, 6, 85, 2700, 1700),
        (2, 7, 85, 2800, 1900),
        (3, 11, 80, 2500, 1700),
        (3, 10, 80, 2400, 1600),
        (10, 9, 80, 2300, 1500),
    ]

    for u, v, spd, cap, vol in conns:
        n1, n2 = net.nodes[u], net.nodes[v]
        dist = round(haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon) * 1.15, 1)
        net.add_edge(Edge(u, v, max(10.0, dist), spd, cap, vol, road_type="highway"), bidirectional=True)

    return net


def create_west_india_network() -> RoadNetwork:
    """West India Regional Logistics Corridor."""
    net = RoadNetwork("West India Regional Logistics Corridor")
    cities = [
        (0, "Mumbai JNPT Port Freight Hub (Depot)", 19.0760, 72.8777, True, 0.0, 0, 86400),
        (1, "Pune Auto & IT Corridor", 18.5204, 73.8567, False, 36.0, 27000, 39600),
        (2, "Ahmedabad Sanand & Naroda SEZ", 23.0225, 72.5714, False, 38.0, 28800, 43200),
        (3, "Surat Diamond Bourse & Hazira", 21.1702, 72.8311, False, 32.0, 27000, 41400),
        (4, "Vadodara Petrochemical Hub", 22.3072, 73.1812, False, 26.0, 28800, 41400),
        (5, "Nagpur MIHAN Multi-Modal Hub", 21.1458, 79.0882, False, 40.0, 30600, 46800),
        (6, "Nashik Ozar Engineering Center", 19.9975, 73.7898, False, 22.0, 28800, 39600),
        (7, "Indore Pithampur Auto Cluster", 22.7196, 75.8577, False, 30.0, 30600, 45000),
        (8, "Bhopal Mandideep Industrial Node", 23.2599, 77.4126, False, 25.0, 30600, 45000),
        (9, "Panaji Mormugao Port Goa", 15.4909, 73.8278, False, 20.0, 32400, 48600),
        (10, "Rajkot Engineering & Metoda GIDC", 22.3039, 70.8022, False, 24.0, 30600, 45000),
        (11, "Chhatrapati Sambhajinagar Shendra DMIC", 19.8762, 75.3433, False, 22.0, 28800, 41400),
    ]

    for c in cities:
        net.add_node(Node(c[0], c[2], c[3], c[1], c[4], c[5], float(c[6]), float(c[7])))

    conns = [
        (0, 1, 100, 3800, 2900),
        (0, 6, 85, 2800, 1900),
        (0, 3, 85, 3600, 2700),
        (3, 4, 90, 3200, 2300),
        (4, 2, 100, 3500, 2400),
        (2, 10, 85, 2600, 1700),
        (0, 5, 110, 4000, 2500),
        (6, 11, 80, 2200, 1500),
        (11, 5, 90, 2800, 1800),
        (1, 9, 80, 2400, 1600),
        (0, 9, 75, 2200, 1500),
        (4, 7, 85, 2600, 1700),
        (7, 8, 90, 2800, 1800),
        (7, 5, 80, 2200, 1400),
    ]

    for u, v, spd, cap, vol in conns:
        n1, n2 = net.nodes[u], net.nodes[v]
        dist = round(haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon) * 1.15, 1)
        net.add_edge(Edge(u, v, max(10.0, dist), spd, cap, vol, road_type="highway"), bidirectional=True)

    return net


def create_east_northeast_network() -> RoadNetwork:
    """East & Northeast India Regional Logistics Corridor."""
    net = RoadNetwork("East & Northeast India Logistics Corridor")
    cities = [
        (0, "Kolkata Dankuni Freight Terminal (Depot)", 22.5726, 88.3639, True, 0.0, 0, 86400),
        (1, "Bhubaneswar Mancheswar Industrial Area", 20.2961, 85.8245, False, 32.0, 28800, 43200),
        (2, "Patna Fatuha Multi-Modal Terminal", 25.5941, 85.1376, False, 35.0, 28800, 43200),
        (3, "Ranchi Namkum Industrial Area", 23.3441, 85.3096, False, 28.0, 28800, 41400),
        (4, "Jamshedpur Adityapur Auto Complex", 22.8046, 86.2029, False, 30.0, 27000, 39600),
        (5, "Siliguri North Bengal Transport Hub", 26.7271, 88.3953, False, 34.0, 30600, 46800),
        (6, "Guwahati North Guwahati Inland Port", 26.1445, 91.7362, False, 38.0, 32400, 50400),
        (7, "Shillong Byrnihat Industrial Corridor", 25.5788, 91.8933, False, 18.0, 34200, 52200),
        (8, "Durgapur Steel City Hub", 23.5204, 87.3119, False, 24.0, 27000, 37800),
        (9, "Asansol Burnpur Engineering Node", 23.6889, 86.9661, False, 22.0, 28800, 39600),
        (10, "Cuttack Jagatpur Industrial Estate", 20.4625, 85.8828, False, 20.0, 28800, 43200),
        (11, "Agartala Integrated Checkpost Hub", 23.8315, 91.2868, False, 20.0, 36000, 54000),
    ]

    for c in cities:
        net.add_node(Node(c[0], c[2], c[3], c[1], c[4], c[5], float(c[6]), float(c[7])))

    conns = [
        (0, 1, 85, 3000, 2100),
        (1, 10, 75, 2400, 1600),
        (0, 4, 85, 2600, 1800),
        (4, 3, 80, 2200, 1500),
        (0, 8, 90, 3000, 2000),
        (8, 9, 85, 2600, 1700),
        (9, 3, 80, 2200, 1400),
        (9, 2, 80, 2400, 1600),
        (0, 5, 80, 2500, 1700),
        (5, 6, 80, 2400, 1600),
        (6, 7, 70, 1800, 1200),
        (6, 11, 65, 1600, 1100),
    ]

    for u, v, spd, cap, vol in conns:
        n1, n2 = net.nodes[u], net.nodes[v]
        dist = round(haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon) * 1.15, 1)
        net.add_edge(Edge(u, v, max(10.0, dist), spd, cap, vol, road_type="highway"), bidirectional=True)

    return net


# =====================================================================
# Detailed Metropolitan Road Networks
# =====================================================================

def create_mumbai_network() -> RoadNetwork:
    """Mumbai Metropolitan Region (MMR) Urban Logistics Network."""
    net = RoadNetwork("Mumbai Metropolitan Region (MMR) Logistics Network")
    locations = [
        (0, "Bandra Kurla Complex (BKC Freight Hub)", 19.0657, 72.8687, True, 0.0, 0, 86400),
        (1, "Nariman Point Business District", 18.9256, 72.8242, False, 22.0, 27000, 36000),
        (2, "Dadar TT Circle Terminal", 19.0178, 72.8478, False, 20.0, 28800, 37800),
        (3, "Andheri MIDC Industrial Hub", 19.1197, 72.8697, False, 30.0, 28800, 39600),
        (4, "Borivali Western Express Node", 19.2288, 72.8541, False, 25.0, 30600, 41400),
        (5, "Powai Hiranandani Tech Zone", 19.1197, 72.9051, False, 24.0, 28800, 39600),
        (6, "Vashi APMC Wholesale Market", 19.0771, 72.9986, False, 40.0, 27000, 37800),
        (7, "Thane Wagle Industrial Estate", 19.2183, 72.9781, False, 32.0, 30600, 43200),
        (8, "JNPT Sea Port Logistics Park", 18.9499, 72.9515, False, 50.0, 27000, 45000),
        (9, "Belapur CBD Central Terminal", 19.0144, 73.0400, False, 20.0, 30600, 41400),
        (10, "Goregaon NESCO Exhibition Hub", 19.1551, 72.8550, False, 18.0, 28800, 39600),
        (11, "Kurla Phoenix Marketcity Hub", 19.0860, 72.8890, False, 22.0, 28800, 37800),
    ]

    for c in locations:
        net.add_node(Node(c[0], c[2], c[3], c[1], c[4], c[5], float(c[6]), float(c[7])))

    conns = [
        (0, 11, 50, 1800, 1300),
        (11, 2, 50, 1800, 1400),
        (2, 1, 55, 1900, 1500),
        (0, 3, 50, 1900, 1450),
        (3, 10, 50, 1800, 1350),
        (10, 4, 55, 1900, 1400),
        (0, 5, 45, 1600, 1200),
        (5, 7, 50, 1800, 1350),
        (0, 6, 60, 2200, 1600),
        (6, 7, 55, 2000, 1450),
        (6, 9, 60, 2100, 1500),
        (9, 8, 65, 2400, 1650),
        (6, 8, 65, 2300, 1600),
    ]

    for u, v, spd, cap, vol in conns:
        n1, n2 = net.nodes[u], net.nodes[v]
        dist = round(haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon) * 1.12, 2)
        net.add_edge(Edge(u, v, max(1.0, dist), spd, cap, vol, road_type="primary"), bidirectional=True)

    return net


def create_chennai_network() -> RoadNetwork:
    """Chennai Metropolitan Road & Port Network."""
    net = RoadNetwork("Chennai Metropolitan Road & Port Network")
    locations = [
        (0, "Chennai Central Port Logistics Hub (Depot)", 13.0827, 80.2707, True, 0.0, 0, 86400),
        (1, "Guindy Industrial Estate Hub", 13.0067, 80.2025, False, 28.0, 27000, 36000),
        (2, "OMR Tidel Park IT Corridor", 12.9892, 80.2486, False, 32.0, 28800, 39600),
        (3, "Siruseri SIPCOT IT SEZ", 12.8337, 80.2198, False, 35.0, 30600, 43200),
        (4, "Sriperumbudur Auto Hub", 12.9719, 79.9427, False, 45.0, 30600, 45000),
        (5, "Anna Nagar West Terminal", 13.0850, 80.2100, False, 20.0, 28800, 37800),
        (6, "T. Nagar Commercial Center", 13.0418, 80.2341, False, 22.0, 28800, 36000),
        (7, "Tambaram Railway Logistics Hub", 12.9249, 80.1000, False, 26.0, 30600, 41400),
        (8, "Ennore Port Maritime Gateway", 13.2300, 80.3200, False, 40.0, 27000, 43200),
        (9, "Ambattur Industrial Estate", 13.1143, 80.1548, False, 30.0, 28800, 39600),
        (10, "Velachery Hub", 12.9815, 80.2180, False, 20.0, 28800, 37800),
        (11, "Poonamallee Bypass Terminal", 13.0489, 80.0933, False, 24.0, 30600, 41400),
    ]

    for c in locations:
        net.add_node(Node(c[0], c[2], c[3], c[1], c[4], c[5], float(c[6]), float(c[7])))

    conns = [
        (0, 8, 60, 2200, 1500),
        (0, 5, 50, 1800, 1300),
        (0, 6, 50, 1900, 1400),
        (6, 1, 55, 2000, 1450),
        (1, 2, 50, 1900, 1400),
        (2, 10, 45, 1600, 1200),
        (2, 3, 65, 2400, 1700),
        (1, 7, 60, 2200, 1600),
        (7, 3, 55, 1900, 1350),
        (5, 9, 50, 1800, 1300),
        (9, 11, 55, 1900, 1350),
        (11, 4, 70, 2600, 1750),
        (7, 4, 65, 2300, 1600),
    ]

    for u, v, spd, cap, vol in conns:
        n1, n2 = net.nodes[u], net.nodes[v]
        dist = round(haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon) * 1.12, 2)
        net.add_edge(Edge(u, v, max(1.0, dist), spd, cap, vol, road_type="primary"), bidirectional=True)

    return net


def create_hyderabad_network() -> RoadNetwork:
    """Hyderabad Metropolitan & Cyberabad Road Network."""
    net = RoadNetwork("Hyderabad Cyberabad Logistics Network")
    locations = [
        (0, "Secunderabad Central Freight Terminal (Depot)", 17.4399, 78.4983, True, 0.0, 0, 86400),
        (1, "HITEC City Cyber Towers", 17.4504, 78.3808, False, 36.0, 28800, 39600),
        (2, "Gachibowli Financial District", 17.4401, 78.3489, False, 34.0, 28800, 39600),
        (3, "Begumpet Central Junction", 17.4448, 78.4664, False, 20.0, 27000, 36000),
        (4, "Shamshabad RGIA Cargo Terminal", 17.2403, 78.4294, False, 45.0, 30600, 45000),
        (5, "Charminar Old City Center", 17.3616, 78.4747, False, 22.0, 28800, 36000),
        (6, "Uppal Industrial & Metro Hub", 17.4018, 78.5602, False, 26.0, 28800, 39600),
        (7, "Kukatpally Housing Board (KPHB)", 17.4938, 78.3995, False, 28.0, 28800, 39600),
        (8, "Madhapur IT Hub", 17.4483, 78.3915, False, 30.0, 28800, 37800),
        (9, "Mehdipatnam Commercial Node", 17.3916, 78.4400, False, 24.0, 28800, 37800),
        (10, "Miyapur Metro Industrial Depot", 17.4968, 78.3548, False, 25.0, 30600, 41400),
        (11, "LB Nagar South-East Gateway", 17.3457, 78.5522, False, 26.0, 30600, 43200),
    ]

    for c in locations:
        net.add_node(Node(c[0], c[2], c[3], c[1], c[4], c[5], float(c[6]), float(c[7])))

    conns = [
        (0, 3, 50, 1800, 1300),
        (3, 7, 55, 2000, 1450),
        (7, 10, 55, 1900, 1350),
        (10, 1, 55, 2000, 1400),
        (1, 8, 45, 1600, 1250),
        (1, 2, 60, 2200, 1600),
        (2, 4, 80, 3000, 2000),
        (3, 9, 50, 1800, 1300),
        (9, 5, 45, 1500, 1200),
        (5, 4, 75, 2800, 1900),
        (0, 6, 55, 1900, 1350),
        (6, 11, 60, 2100, 1450),
        (11, 4, 80, 3000, 2100),
    ]

    for u, v, spd, cap, vol in conns:
        n1, n2 = net.nodes[u], net.nodes[v]
        dist = round(haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon) * 1.12, 2)
        net.add_edge(Edge(u, v, max(1.0, dist), spd, cap, vol, road_type="primary"), bidirectional=True)

    return net


def create_kolkata_network() -> RoadNetwork:
    """Kolkata Metropolitan Road Network."""
    net = RoadNetwork("Kolkata Metropolitan & IT Hub Network")
    locations = [
        (0, "Howrah Station Central Freight Depot", 22.5850, 88.3426, True, 0.0, 0, 86400),
        (1, "Salt Lake Sector V IT Hub", 22.5697, 88.4334, False, 35.0, 28800, 39600),
        (2, "New Town Action Area I & II", 22.5898, 88.4744, False, 32.0, 30600, 43200),
        (3, "Park Street Commercial District", 22.5535, 88.3519, False, 20.0, 27000, 36000),
        (4, "Burrabazar Wholesale Trading Core", 22.5800, 88.3550, False, 30.0, 27000, 36000),
        (5, "Taratala & Hyde Road Logistics SEZ", 22.5126, 88.3150, False, 40.0, 28800, 41400),
        (6, "Dum Dum Airport Cargo Complex", 22.6520, 88.4463, False, 38.0, 28800, 43200),
        (7, "Sealdah Rail Terminal Hub", 22.5675, 88.3712, False, 25.0, 27000, 36000),
        (8, "Shyambazar Five-Point Crossing", 22.6025, 88.3716, False, 18.0, 28800, 37800),
        (9, "Gariahat South Kolkata Market", 22.5186, 88.3686, False, 22.0, 28800, 37800),
        (10, "Dankuni Multi-Modal Freight Terminal", 22.6780, 88.2930, False, 45.0, 27000, 45000),
        (11, "Rajarhat Eco Park Logistics", 22.6100, 88.4680, False, 24.0, 30600, 43200),
    ]

    for c in locations:
        net.add_node(Node(c[0], c[2], c[3], c[1], c[4], c[5], float(c[6]), float(c[7])))

    conns = [
        (0, 4, 40, 1400, 1100),
        (4, 7, 45, 1500, 1200),
        (0, 10, 65, 2400, 1600),
        (10, 8, 55, 1900, 1350),
        (8, 6, 60, 2100, 1450),
        (6, 2, 60, 2200, 1500),
        (2, 11, 55, 1900, 1300),
        (2, 1, 55, 2000, 1400),
        (1, 7, 50, 1800, 1300),
        (7, 3, 45, 1600, 1250),
        (3, 9, 45, 1600, 1200),
        (3, 5, 50, 1800, 1350),
        (5, 9, 45, 1500, 1150),
    ]

    for u, v, spd, cap, vol in conns:
        n1, n2 = net.nodes[u], net.nodes[v]
        dist = round(haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon) * 1.12, 2)
        net.add_edge(Edge(u, v, max(1.0, dist), spd, cap, vol, road_type="primary"), bidirectional=True)

    return net


def create_pune_network() -> RoadNetwork:
    """Pune Industrial & Automotive Corridor."""
    net = RoadNetwork("Pune Industrial & IT Corridors")
    locations = [
        (0, "Shivajinagar Central Depot", 18.5314, 73.8446, True, 0.0, 0, 86400),
        (1, "Hinjawadi Phase 1 IT Park", 18.5913, 73.7389, False, 35.0, 28800, 39600),
        (2, "Hinjawadi Phase 3 Megapolis", 18.5800, 73.6900, False, 30.0, 30600, 41400),
        (3, "Chakan MIDC Auto Hub", 18.7606, 73.8567, False, 45.0, 30600, 45000),
        (4, "Bhosari Industrial Estate", 18.6298, 73.8440, False, 32.0, 28800, 39600),
        (5, "Hadapsar Magarpatta Cybercity", 18.5089, 73.9259, False, 28.0, 28800, 37800),
        (6, "Viman Nagar & Airport Hub", 18.5679, 73.9143, False, 25.0, 28800, 37800),
        (7, "Kothrud Commercial Zone", 18.5074, 73.8077, False, 20.0, 27000, 36000),
        (8, "Talegaon Auto Cluster", 18.7300, 73.6800, False, 30.0, 32400, 45000),
        (9, "Pimpri Auto Manufacturing", 18.6279, 73.8009, False, 34.0, 28800, 39600),
        (10, "Swargate South Hub", 18.5018, 73.8636, False, 18.0, 27000, 36000),
        (11, "Kharadi EON Free Zone", 18.5515, 73.9530, False, 28.0, 30600, 41400),
    ]

    for c in locations:
        net.add_node(Node(c[0], c[2], c[3], c[1], c[4], c[5], float(c[6]), float(c[7])))

    conns = [
        (0, 7, 50, 1800, 1300),
        (0, 10, 45, 1600, 1200),
        (0, 9, 55, 2000, 1450),
        (9, 4, 55, 1900, 1350),
        (4, 3, 65, 2400, 1700),
        (9, 1, 55, 2000, 1450),
        (1, 2, 50, 1800, 1300),
        (1, 8, 65, 2200, 1500),
        (8, 3, 60, 2100, 1450),
        (0, 6, 50, 1800, 1350),
        (6, 11, 55, 1900, 1400),
        (11, 5, 50, 1800, 1300),
        (5, 10, 45, 1600, 1200),
    ]

    for u, v, spd, cap, vol in conns:
        n1, n2 = net.nodes[u], net.nodes[v]
        dist = round(haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon) * 1.12, 2)
        net.add_edge(Edge(u, v, max(1.0, dist), spd, cap, vol, road_type="primary"), bidirectional=True)

    return net


def create_ahmedabad_network() -> RoadNetwork:
    """Ahmedabad & Gandhinagar Industrial Corridor."""
    net = RoadNetwork("Ahmedabad & Gandhinagar Industrial Network")
    locations = [
        (0, "Kalupur Central Railway Logistics (Depot)", 23.0267, 72.5975, True, 0.0, 0, 86400),
        (1, "SG Highway Corporate Corridor", 23.0384, 72.5120, False, 30.0, 28800, 39600),
        (2, "Sanand Auto Manufacturing GIDC", 22.9900, 72.3800, False, 45.0, 30600, 45000),
        (3, "Naroda GIDC Industrial Hub", 23.0780, 72.6550, False, 36.0, 28800, 39600),
        (4, "Changodar Logistics & Freight SEZ", 22.9200, 72.4400, False, 40.0, 28800, 43200),
        (5, "Prahlad Nagar Commercial Core", 23.0120, 72.5100, False, 22.0, 28800, 37800),
        (6, "Gandhinagar GIFT City & Infocity", 23.1600, 72.6800, False, 35.0, 30600, 43200),
        (7, "Ashram Road Business District", 23.0350, 72.5700, False, 18.0, 27000, 36000),
        (8, "Maninagar South Terminal", 22.9970, 72.6030, False, 20.0, 27000, 36000),
        (9, "Bopal Western Residential/Commercial", 23.0330, 72.4670, False, 24.0, 30600, 41400),
        (10, "Vatva GIDC Chemical Zone", 22.9600, 72.6300, False, 32.0, 28800, 41400),
        (11, "Sarkhej Logistics Interchange", 22.9800, 72.5000, False, 26.0, 28800, 39600),
    ]

    for c in locations:
        net.add_node(Node(c[0], c[2], c[3], c[1], c[4], c[5], float(c[6]), float(c[7])))

    conns = [
        (0, 7, 50, 1800, 1300),
        (7, 1, 55, 2000, 1450),
        (1, 5, 55, 1900, 1400),
        (1, 9, 50, 1800, 1300),
        (9, 2, 65, 2400, 1650),
        (5, 11, 55, 1900, 1350),
        (11, 4, 70, 2600, 1800),
        (0, 8, 45, 1600, 1200),
        (8, 10, 50, 1800, 1350),
        (0, 3, 55, 2000, 1450),
        (3, 6, 65, 2400, 1600),
        (1, 6, 65, 2500, 1700),
    ]

    for u, v, spd, cap, vol in conns:
        n1, n2 = net.nodes[u], net.nodes[v]
        dist = round(haversine_distance_km(n1.lat, n1.lon, n2.lat, n2.lon) * 1.12, 2)
        net.add_edge(Edge(u, v, max(1.0, dist), spd, cap, vol, road_type="primary"), bidirectional=True)

    return net
