from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import service
from .schemas import OptimizeRequest, OptimizeResponse, ScenarioOut
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
