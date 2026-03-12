from enum import Enum


class PackageCategory(str, Enum):
    STRATEGIC = "A"
    MEDICAL = "B"
    FOOD = "C"
    ECONOMIC = "D"
    PERSONAL = "E"


CATEGORY_BASE_FEES = {
    "A": 0,
    "B": 0,
    "C": 2,
    "D": 5,
    "E": 10,
}

WEIGHT_FEE_BRACKETS = [
    (5, 0.5),
    (20, 1.0),
    (75, 2.0),
    (400, 3.0),
    (500, 5.0),
    (float("inf"), 7.0),
]

ADDITIONAL_WAGON_FEE = 55
STANDARD_WAGON_CAPACITY = 500
STANDARD_WAGONS_IN_COMPOSITION = 2
MAX_WEIGHT_KG = 4000

CLOSED_ROUTE_DESTINATIONS = ["Żarnowiec"]
CLOSED_ROUTE_ALLOWED_CATEGORIES = ["A", "B"]

REGIONAL_BOUNDARY_ROUTE_RATES = {
    0: 1.0,
    1: 2.0,
    2: 3.0,
}

CITY_REGIONS = {
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
