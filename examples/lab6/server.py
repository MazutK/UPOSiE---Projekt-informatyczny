"""Lab 6 — opcjonalny przykład z instrukcji: FastAPI nad funkcją forecast.

Uruchomienie (z katalogu repozytorium):
    python -m uvicorn examples.lab6.server:app --host 127.0.0.1 --port 8000

Tylko lokalnie, na dozwolonej próbce: brak zapisu, uwierzytelniania i limitów.
Projektowe API jest w apps/api (to jest osobne ćwiczenie).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .forecast import UNIT, forecast

app = FastAPI(title="Prognoza zgłoszeń")


class ForecastInput(BaseModel):
    model_config = ConfigDict(strict=True, allow_inf_nan=False, extra="forbid")

    history: list[float]
    window: int = Field(gt=0)


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    if any(error.get("type") == "json_invalid" for error in exc.errors()):
        return JSONResponse(status_code=400, content={"error": "invalid_json"})
    return JSONResponse(status_code=422, content={"error": "invalid_history"})


@app.post("/api/forecast")
def api_forecast(data: ForecastInput):
    try:
        value = forecast(list(data.history), data.window)
    except (ValueError, OverflowError):
        return JSONResponse(status_code=422, content={"error": "invalid_history"})
    return {"forecast": value, "unit": UNIT, "window": data.window}
