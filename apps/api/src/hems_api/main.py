from __future__ import annotations

import math
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import service
from .schemas import (
    CompareRequest,
    CompareResponse,
    LiveDayResponse,
    OptimizeRequest,
    OptimizeResponse,
    ScenarioOut,
    SensitivityRequest,
    SensitivityResponse,
)
from .settings import settings

app = FastAPI(
    title="Optymalizator ogrzewania - API",
    version="0.2.0",
    description="Warstwa HTTP nad pakietem heating_optimizer.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _json_safe(value: Any) -> Any:
    """NaN/Infinity nie da się zapisać w JSON — zamieniamy je na tekst."""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    return value


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Z-03: ten sam kształt co domyślny błąd FastAPI (422, lista w `detail`),
    ale bez wywrotki serializacji, gdy żądanie zawiera NaN."""
    return JSONResponse(status_code=422, content={"detail": _json_safe(jsonable_encoder(exc.errors()))})


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": app.version}


@app.get("/api/scenarios", response_model=list[ScenarioOut])
def scenarios() -> list[ScenarioOut]:
    return service.list_scenarios()


@app.post("/api/optimize", response_model=OptimizeResponse)
def optimize(request: OptimizeRequest) -> OptimizeResponse:
    try:
        return service.optimize(request)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.post("/api/compare", response_model=CompareResponse)
def compare(request: CompareRequest) -> CompareResponse:
    try:
        return service.compare(request)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.post("/api/sensitivity", response_model=SensitivityResponse)
def sensitivity(request: SensitivityRequest) -> SensitivityResponse:
    try:
        return service.sensitivity(request)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.get("/api/live", response_model=LiveDayResponse)
def live(
    date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
) -> LiveDayResponse:
    try:
        return service.get_live_day(date)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Błąd pobierania danych live: {e}") from e
