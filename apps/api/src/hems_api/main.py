from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

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
