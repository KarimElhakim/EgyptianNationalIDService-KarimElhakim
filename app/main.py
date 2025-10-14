"""FastAPI application exposing Egyptian National ID utilities."""

from __future__ import annotations

from datetime import date

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import settings
from .database import database
from .national_id import NationalIDDetails, NationalIDValidationError, parse_national_id
from .security import get_current_api_key


class NationalIDRequest(BaseModel):
    national_id: str = Field(..., example="29001011234567")


class NationalIDDetailsResponse(BaseModel):
    birth_date: date
    gender: str
    governorate_code: str
    governorate_name: str

    @classmethod
    def from_domain(cls, details: NationalIDDetails) -> "NationalIDDetailsResponse":
        return cls(
            birth_date=details.birth_date,
            gender=details.gender,
            governorate_code=details.governorate_code,
            governorate_name=details.governorate_name,
        )


class NationalIDSuccessResponse(BaseModel):
    national_id: str
    valid: bool = True
    details: NationalIDDetailsResponse


class ErrorResponse(BaseModel):
    national_id: str
    valid: bool = False
    error: str


class UsageResponse(BaseModel):
    api_key: str
    owner: str
    total_requests: int


app = FastAPI(title="Egyptian National ID Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def initialise_database() -> None:
    database.initialise(settings.default_api_keys, settings.api_rate_limit_per_minute)


@app.post(
    "/v1/national-ids/inspect",
    response_model=NationalIDSuccessResponse,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}},
)
def inspect_national_id(
    payload: NationalIDRequest,
    _: dict[str, object] = Depends(get_current_api_key()),
) -> NationalIDSuccessResponse | JSONResponse:
    try:
        details = parse_national_id(payload.national_id)
    except NationalIDValidationError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "national_id": payload.national_id,
                "valid": False,
                "error": str(exc),
            },
        )

    return NationalIDSuccessResponse(
        national_id=payload.national_id,
        details=NationalIDDetailsResponse.from_domain(details),
    )


@app.get("/v1/usage", response_model=UsageResponse)
def get_usage(api_key=Depends(get_current_api_key(increment_usage=False))) -> UsageResponse:
    total_requests = database.get_usage(api_key["key"])
    return UsageResponse(
        api_key=api_key["key"],
        owner=str(api_key.get("owner", "")),
        total_requests=total_requests or 0,
    )
