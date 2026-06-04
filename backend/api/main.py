"""
EV Battery Range Estimator — Hyperscale FastAPI Backend
"""

import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from configs.config import settings
from backend.api.routes import router
from backend.api.middleware.timing import timing_middleware

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from streaming.websockets.router import router as ws_router

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# OpenTelemetry Setup
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    SimpleSpanProcessor(ConsoleSpanExporter())
)

app = FastAPI(
    title="EV Battery Range Estimator Global Infrastructure",
    description="Hyperscale AI Mesh with OpenTelemetry, Kafka streaming, and ONNX acceleration.",
    version="3.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BaseHTTPMiddleware, dispatch=timing_middleware)

from fastapi.staticfiles import StaticFiles

# Instrument Prometheus Metrics
Instrumentator().instrument(app).expose(app)

app.include_router(router)
app.include_router(ws_router)

# Mount compiled React assets
assets_path = os.path.join(settings.PROJECT_ROOT, "frontend", "range-map-react", "dist", "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

@app.get("/")
@limiter.limit("10/minute")
def root(request: Request):
    landing_path = os.path.join(settings.PROJECT_ROOT, "frontend", "web", "landing.html")
    return FileResponse(landing_path)

@app.get("/console")
@limiter.limit("10/minute")
def console(request: Request):
    frontend_path = os.path.join(settings.PROJECT_ROOT, "frontend", "range-map-react", "dist", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    # Graceful fallback to legacy web client if React app is not compiled
    legacy_path = os.path.join(settings.PROJECT_ROOT, "frontend", "web", "index.html")
    return FileResponse(legacy_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=False)

