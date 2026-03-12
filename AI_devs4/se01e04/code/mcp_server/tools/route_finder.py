import re
from typing import Optional


CLOSED_ROUTE_DESTINATIONS = ["Żarnowiec"]
CLOSED_ROUTE_ALLOWED_CATEGORIES = ["A", "B"]

CITY_CONNECTIONS = {
    "Gdańsk": {"R-01": "Bydgoszcz", "R-16": "Elbląg", "M-10": "Poznań"},
    "Żarnowiec": {"X-01": "Gdańsk"},
    "Bydgoszcz": {"R-02": "Toruń", "R-18": "Toruń"},
    "Elbląg": {"R-17": "Olsztyn"},
    "Poznań": {"M-04": "Warszawa", "R-04": "Zielona Góra"},
    "Toruń": {"R-03": "Gdańsk"},
    "Olsztyn": {"R-06": "Elbląg"},
    "Warszawa": {"M-05": "Łódź", "M-06": "Białystok", "M-01": "Łódź"},
    "Łódź": {"M-02": "Warszawa", "R-11": "Częstochowa"},
    "Zielona Góra": {"R-05": "Wrocław"},
    "Białystok": {"R-12": "Lublin"},
    "Częstochowa": {"R-20": "Wrocław", "R-10": "Katowice"},
    "Wrocław": {"M-08": "Kraków", "R-20": "Częstochowa"},
    "Katowice": {"M-07": "Kraków", "R-07": "Kielce"},
    "Kraków": {"M-14": "Rzeszów", "M-08": "Wrocław"},
    "Kielce": {"R-08": "Radom", "R-07": "Katowice"},
    "Radom": {"R-09": "Warszawa"},
    "Lublin": {"M-15": "Rzeszów", "R-12": "Białystok"},
    "Rzeszów": {"R-19": "Rzeszów", "M-14": "Kraków", "M-15": "Lublin"},
    "Szczecin": {"R-13": "Gdańsk"},
}

REGIONAL_BOUNDARIES = {
    ("Gdańsk", "Żarnowiec"): 0,
    ("Żarnowiec", "Gdańsk"): 0,
}

REGION_MAP = {
    "Gdańsk": "Pomeranian",
    "Żarnowiec": "Pomeranian",
    "Bydgoszcz": "Kuyavian-Pomeranian",
    "Toruń": "Kuyavian-Pomeranian",
    "Elbląg": "Warmian-Masurian",
    "Olsztyn": "Warmian-Masurian",
    "Warszawa": "Masovian",
    "Łódź": "Łódź",
    "Częstochowa": "Silesian",
    "Kraków": "Lesser Poland",
    "Wrocław": "Lower Silesian",
    "Katowice": "Silesian",
    "Kielce": "Świętokrzyskie",
    "Radom": "Masovian",
    "Białystok": "Podlaskie",
    "Lublin": "Lublin",
    "Rzeszów": "Subcarpathian",
    "Zielona Góra": "Lubusz",
    "Poznań": "Greater Poland",
    "Szczecin": "West Pomeranian",
}

ESTIMATED_DISTANCES = {
    ("Gdańsk", "Żarnowiec"): 40,
    ("Żarnowiec", "Gdańsk"): 40,
}


def get_regional_boundaries(origin: str, destination: str) -> int:
    if (origin, destination) in REGIONAL_BOUNDARIES:
        return REGIONAL_BOUNDARIES[(origin, destination)]

    origin_region = REGION_MAP.get(origin)
    dest_region = REGION_MAP.get(destination)

    if origin_region == dest_region:
        return 0
    return 1


def get_distance(origin: str, destination: str) -> float:
    if (origin, destination) in ESTIMATED_DISTANCES:
        return ESTIMATED_DISTANCES[(origin, destination)]
    return 50.0


class RouteFinder:
    def __init__(
        self, route_diagram_path: str = None, closed_routes_image_path: str = None
    ):
        self.route_diagram_path = route_diagram_path
        self.closed_routes_image_path = closed_routes_image_path
        self.connections = CITY_CONNECTIONS

    def find_route(self, origin: str, destination: str, category: str) -> dict:
        uses_closed_route = False
        requires_special_authorization = False

        if destination in CLOSED_ROUTE_DESTINATIONS:
            if category not in CLOSED_ROUTE_ALLOWED_CATEGORIES:
                raise ValueError(
                    f"Destination {destination} is closed. Only categories A/B allowed."
                )
            uses_closed_route = True
            requires_special_authorization = True

        if uses_closed_route and destination == "Żarnowiec":
            route_code = "X-01"
        else:
            route_code = f"{origin[:3].upper()}-{destination[:3].upper()}"

        distance_km = get_distance(origin, destination)
        regional_boundaries = get_regional_boundaries(origin, destination)

        return {
            "route_code": route_code,
            "distance_km": distance_km,
            "regional_boundaries": regional_boundaries,
            "uses_closed_route": uses_closed_route,
            "requires_special_authorization": requires_special_authorization,
        }
