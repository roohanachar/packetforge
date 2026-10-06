"""
FastAPI application for Intelligent IPv4 Fragmentation & Network Failure Simulator.

Exposes REST endpoints to simulate IPv4 packet fragmentation, transmission under
configured network failures, and logical reassembly.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from backend.core.simulator import PacketSimulator
from .schemas import HealthResponse, SimulationRequest, SimulationResponse

app = FastAPI(
    title="Intelligent IPv4 Fragmentation & Network Failure Simulator API",
    description="HTTP API for simulating IPv4 fragmentation, transmission failures, and reassembly.",
    version="1.0.0",
)

# CORS configuration allowing explicit Vite frontend origins
origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/api/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Health check endpoint",
)
def health_check() -> HealthResponse:
    """Returns the operational status of the API."""
    return HealthResponse(status="ok")


@app.post(
    "/api/simulate",
    response_model=SimulationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Simulation"],
    summary="Run an end-to-end packet simulation",
)
def simulate(request: SimulationRequest) -> SimulationResponse:
    """
    Executes the unified IPv4 packet simulation pipeline:
    1. Splits the original packet into fragments based on link MTU.
    2. Simulates transmission conditions (delay, drops, duplicates, corruption, reordering).
    3. Reassembles the delivered fragments and checks integrity.
    4. Returns a comprehensive result payload for visualization.
    """
    try:
        config = request.to_core()
        result = PacketSimulator.simulate(config)
        return SimulationResponse.from_core(result, df=request.df)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
