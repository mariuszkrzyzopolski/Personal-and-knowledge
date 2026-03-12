import math
from core.constants import (
    CATEGORY_BASE_FEES,
    WEIGHT_FEE_BRACKETS,
    ADDITIONAL_WAGON_FEE,
    STANDARD_WAGON_CAPACITY,
    STANDARD_WAGONS_IN_COMPOSITION,
    REGIONAL_BOUNDARY_ROUTE_RATES,
)


def calculate_weight_fee(weight_kg: float, category: str) -> float:
    if category in ["A", "B"]:
        return 0.0

    weight_fee = 0.0
    remaining_weight = weight_kg

    for max_weight, rate in WEIGHT_FEE_BRACKETS:
        if remaining_weight <= 0:
            break
        bracket_weight = min(remaining_weight, max_weight)
        weight_fee += bracket_weight * rate
        remaining_weight -= bracket_weight

    return weight_fee


def calculate_route_fee(
    distance_km: float, regional_boundaries: int, category: str
) -> float:
    if category in ["A", "B"]:
        return 0.0

    rate = REGIONAL_BOUNDARY_ROUTE_RATES.get(regional_boundaries, 3.0)
    return (distance_km / 100) * rate


def calculate_additional_wagons(weight_kg: float, category: str) -> tuple[int, float]:
    if weight_kg <= STANDARD_WAGON_CAPACITY:
        return 0, 0.0

    wagons_needed = math.ceil(weight_kg / STANDARD_WAGON_CAPACITY)
    additional_wagons = max(0, wagons_needed - STANDARD_WAGONS_IN_COMPOSITION)

    if category in ["A", "B"]:
        return additional_wagons, 0.0

    return additional_wagons, additional_wagons * ADDITIONAL_WAGON_FEE


def calculate_wdp(weight_kg: float, category: str) -> int:
    if weight_kg <= STANDARD_WAGON_CAPACITY:
        return 0

    wagons_needed = math.ceil(weight_kg / STANDARD_WAGON_CAPACITY)
    additional_wagons = wagons_needed - STANDARD_WAGONS_IN_COMPOSITION

    return additional_wagons


class FeeCalculator:
    def __init__(self):
        self.category_base_fees = CATEGORY_BASE_FEES

    def calculate(
        self,
        category: str,
        weight_kg: float,
        distance_km: float,
        regional_boundaries: int,
    ) -> dict:
        base_fee = self.category_base_fees.get(category, 10)

        weight_fee = calculate_weight_fee(weight_kg, category)
        route_fee = calculate_route_fee(distance_km, regional_boundaries, category)
        additional_wagons, additional_wagon_fee = calculate_additional_wagons(
            weight_kg, category
        )

        total = base_fee + weight_fee + route_fee + additional_wagon_fee
        wdp = calculate_wdp(weight_kg, category)

        return {
            "base_fee": base_fee,
            "weight_fee": weight_fee,
            "route_fee": route_fee,
            "additional_wagons": additional_wagons,
            "additional_wagon_fee": additional_wagon_fee,
            "total": total,
            "wdp": wdp,
        }
