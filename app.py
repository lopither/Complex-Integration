from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from complex_math import MathInputError, analyze_complex_function


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


class AnalysisRequest(BaseModel):
    function: str
    contour: str = "exp(i*t)"
    t_min: str = "0"
    t_max: str = "2*pi"
    component: Literal["abs", "real", "imag"] = "abs"
    x_min: float = -3.0
    x_max: float = 3.0
    y_min: float = -3.0
    y_max: float = 3.0
    resolution: int = Field(default=81, ge=31, le=161)
    integral_samples: int = Field(default=4000, ge=600, le=12000)


app = FastAPI(title="Complex Integration Studio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/analyze")
def analyze(request: AnalysisRequest) -> dict:
    try:
        return analyze_complex_function(
            function_text=request.function,
            contour_text=request.contour,
            t_min_text=request.t_min,
            t_max_text=request.t_max,
            component=request.component,
            x_min=request.x_min,
            x_max=request.x_max,
            y_min=request.y_min,
            y_max=request.y_max,
            resolution=request.resolution,
            integral_samples=request.integral_samples,
        )
    except MathInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
