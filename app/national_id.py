"""Core logic for validating and parsing Egyptian National ID numbers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


class NationalIDValidationError(ValueError):
    """Raised when the supplied National ID number is invalid."""


@dataclass(slots=True)
class NationalIDDetails:
    birth_date: date
    gender: str
    governorate_code: str
    governorate_name: str


_GOVERNORATE_CODES: dict[str, str] = {
    "01": "Cairo",
    "02": "Alexandria",
    "03": "Port Said",
    "04": "Suez",
    "11": "Damietta",
    "12": "Dakahlia",
    "13": "Sharkia",
    "14": "Qalyubia",
    "15": "Kafr El Sheikh",
    "16": "Gharbia",
    "17": "Monufia",
    "18": "Beheira",
    "19": "Ismailia",
    "21": "Giza",
    "22": "Beni Suef",
    "23": "Fayoum",
    "24": "Minya",
    "25": "Assiut",
    "26": "Sohag",
    "27": "Qena",
    "28": "Aswan",
    "29": "Luxor",
    "31": "Red Sea",
    "32": "New Valley",
    "33": "Matrouh",
    "34": "North Sinai",
    "35": "South Sinai",
    "88": "Foreign Residents",
}


def parse_national_id(national_id: str) -> NationalIDDetails:
    """Validate and extract structured data from a National ID number."""

    if not isinstance(national_id, str):
        raise NationalIDValidationError("National ID must be provided as a string")

    stripped = national_id.strip()
    if len(stripped) != 14 or not stripped.isdigit():
        raise NationalIDValidationError("National ID must be a 14-digit numeric string")

    century_digit = stripped[0]
    century_map = {"2": 1900, "3": 2000}
    if century_digit not in century_map:
        raise NationalIDValidationError("Unsupported century digit in National ID")

    year = century_map[century_digit] + int(stripped[1:3])
    month = int(stripped[3:5])
    day = int(stripped[5:7])

    try:
        birth_date = date(year, month, day)
    except ValueError as exc:
        raise NationalIDValidationError("Invalid birth date in National ID") from exc

    governorate_code = stripped[7:9]
    governorate_name = _GOVERNORATE_CODES.get(governorate_code)
    if not governorate_name:
        raise NationalIDValidationError("Unknown governorate code in National ID")

    gender_digit = int(stripped[12])
    gender = "male" if gender_digit % 2 else "female"

    return NationalIDDetails(
        birth_date=birth_date,
        gender=gender,
        governorate_code=governorate_code,
        governorate_name=governorate_name,
    )
