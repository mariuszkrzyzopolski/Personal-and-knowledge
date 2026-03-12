from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import date
from typing import Optional


class PackageCategory(str, Enum):
    STRATEGIC = "A"
    MEDICAL = "B"
    FOOD = "C"
    ECONOMIC = "D"
    PERSONAL = "E"


class PackageRequest(BaseModel):
    sender_id: str = Field(..., pattern=r"^\d{9}$")
    origin: str
    destination: str
    weight_kg: float = Field(..., gt=0.0, le=4000.0)
    category: PackageCategory
    content: str = Field(..., max_length=200)
    special_notes: str = "brak"
    budget_pp: float = 0.0

    @validator("destination")
    def validate_zarnowiec_access(cls, v, values):
        if v == "Żarnowiec" and values.get("category") not in [
            PackageCategory.STRATEGIC,
            PackageCategory.MEDICAL,
        ]:
            raise ValueError("Żarnowiec accessible only for Strategic/Medical packages")
        return v


class RouteResult(BaseModel):
    route_code: str
    distance_km: float
    regional_boundaries: int
    uses_closed_route: bool = False
    requires_special_authorization: bool = False


class FeeResult(BaseModel):
    base_fee: float
    weight_fee: float
    route_fee: float
    additional_wagons: int
    additional_wagon_fee: float
    total: float
    wdp: int


class Declaration(BaseModel):
    content: str
    is_valid_format: bool
    date_generated: str
    validation_errors: list[str] = []
