"""
Traffic Models: Dynamic Congestion (BPR), Vehicle Emissions (CMEM), 
Stochastic Incidents, Weather Effects, and Rush-Hour Waves.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Dict, List, Optional, Tuple


class WeatherCondition(str, Enum):
    CLEAR = "clear"
    RAIN = "rain"
    HEAVY_STORM = "heavy_storm"
    FOG = "fog"


@dataclass
class TrafficIncident:
    incident_id: str
    edge_u: int
    edge_v: int
    severity: float  # 0.0 to 1.0 (1.0 = completely blocked)
    delay_seconds: float  # Additional fixed delay
    start_time: float
    duration_seconds: float
    description: str = "Traffic incident"

    def is_active(self, current_time: float) -> bool:
        return self.start_time <= current_time <= (self.start_time + self.duration_seconds)

    def current_delay(self, current_time: float) -> float:
        if not self.is_active(current_time):
            return 0.0
        # Linear decay of delay as incident clears up
        progress = (current_time - self.start_time) / max(1.0, self.duration_seconds)
        decay = max(0.2, 1.0 - progress * 0.8)
        return self.delay_seconds * decay


class BPRCongestionModel:
    """
    Bureau of Public Roads (BPR) link-performance function:
    T(V) = T_0 * [1 + alpha * (V / C)^beta]
    where:
    T_0 = free-flow travel time
    V   = link volume (traffic flow)
    C   = link practical capacity
    alpha, beta = calibration parameters (typically alpha=0.15, beta=4.0)
    """

    def __init__(self, alpha: float = 0.15, beta: float = 4.0):
        self.alpha = alpha
        self.beta = beta

    def travel_time(
        self,
        free_flow_time: float,
        volume: float,
        capacity: float,
        weather: WeatherCondition = WeatherCondition.CLEAR,
        incident_delay: float = 0.0,
    ) -> float:
        if free_flow_time <= 0:
            return 0.0
        
        # Weather impact multipliers on capacity & free flow speed
        weather_capacity_multiplier = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.RAIN: 0.85,
            WeatherCondition.HEAVY_STORM: 0.65,
            WeatherCondition.FOG: 0.80,
        }.get(weather, 1.0)

        effective_capacity = max(1.0, capacity * weather_capacity_multiplier)
        vc_ratio = max(0.0, volume / effective_capacity)

        congestion_multiplier = 1.0 + self.alpha * (vc_ratio ** self.beta)
        # Cap congestion multiplier to reasonable bound (e.g., 6x) to avoid numeric overflow in extremes
        congestion_multiplier = min(congestion_multiplier, 6.0)

        return (free_flow_time * congestion_multiplier) + incident_delay


class CMEMEmissionModel:
    """
    Comprehensive Modal Emission Model (CMEM) approximation for CO2 & Fuel:
    Calculates carbon emissions (grams of CO2) and fuel consumed (liters)
    as a function of distance, mean speed, and road gradient.
    """

    def __init__(self, base_co2_per_km: float = 140.0):
        # Base emission for typical urban delivery van (140g CO2 / km at optimal 60 km/h)
        self.base_co2_per_km = base_co2_per_km

    def calculate_emissions(
        self, distance_km: float, mean_speed_kmh: float, gradient_percent: float = 0.0
    ) -> Dict[str, float]:
        if distance_km <= 0:
            return {"co2_grams": 0.0, "fuel_liters": 0.0}

        # Speed penalty curve: high emissions at stop-and-go (<20 km/h) and high speeds (>90 km/h)
        v = max(5.0, min(120.0, mean_speed_kmh))
        # Quadratic factor minimized around 60 km/h
        speed_factor = 1.0 + 0.0006 * ((v - 60.0) ** 2)
        if v < 30.0:
            # Low speed / idling penalty
            speed_factor += (30.0 - v) * 0.03

        # Gradient penalty (uphill increases fuel, downhill slight regeneration/saving)
        gradient_factor = 1.0 + max(-0.2, gradient_percent * 0.05)

        co2_grams = distance_km * self.base_co2_per_km * speed_factor * gradient_factor
        # 1 liter of diesel yields approx 2640 grams of CO2
        fuel_liters = co2_grams / 2640.0

        return {
            "co2_grams": round(co2_grams, 2),
            "fuel_liters": round(fuel_liters, 3),
        }


class RushHourProfile:
    """
    Time-of-day traffic surge model using dual-peaked sinusoidal wave (Morning & Evening rush hours).
    """

    @staticmethod
    def get_surge_multiplier(sim_time_seconds: float) -> float:
        # Map simulation time into a 24-hour cycle (hours from 0 to 24)
        sim_hours = (sim_time_seconds / 3600.0) % 24.0
        
        # Morning peak around 8:30 (8.5), Evening peak around 18:00 (18.0)
        morning_peak = math.exp(-0.5 * ((sim_hours - 8.5) / 1.5) ** 2)
        evening_peak = math.exp(-0.5 * ((sim_hours - 18.0) / 2.0) ** 2)
        
        # Base factor between 0.8 (off-peak) to 2.2 (peak)
        surge = 0.8 + 1.2 * morning_peak + 1.0 * evening_peak
        return max(0.8, min(surge, 2.5))
