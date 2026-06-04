import os
from fastapi import APIRouter, HTTPException, Request
from backend.api.schemas import PredictRequest, ForecastRequest
from backend.api.services import MLEngineService
from ml.models.registry import ModelRegistry
from mlops.monitoring.drift import DriftMonitor
from backend.api.workers.celery_app import predict_async_task
from slowapi import Limiter
from slowapi.util import get_remote_address
from tenacity import retry, stop_after_attempt, wait_fixed

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/api/health")
def health():
    try:
        reg = ModelRegistry.get_regressor()
        status = "ok" if reg.trained else "not_trained"
    except Exception as e:
        status = f"error: {str(e)}"
    return {"status": status}

@router.get("/api/ready")
def ready():
    # K8s readiness probe. E.g. checks Redis connection.
    return {"status": "ready"}

@router.get("/api/model-metrics")
@limiter.limit("5/minute")
def get_model_metrics(request: Request):
    return MLEngineService.get_metrics()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def _predict_with_retry(features, model_name):
    return MLEngineService.predict_range(features, model_name)

@router.post("/api/predict")
@limiter.limit("100/minute")
def predict(request: Request, req: PredictRequest):
    features = req.model_dump(exclude={"model_name"}) if hasattr(req, "model_dump") else req.dict(exclude={"model_name"})
    try:
        res = _predict_with_retry(features, req.model_name)
        DriftMonitor.record_inference(features, res)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail="Inference service temporarily unavailable.")

@router.post("/api/v2/predict-async")
@limiter.limit("500/minute")
def predict_async(request: Request, req: PredictRequest):
    features = req.model_dump(exclude={"model_name"}) if hasattr(req, "model_dump") else req.dict(exclude={"model_name"})
    task = predict_async_task.delay(features, req.model_name)
    return {"task_id": task.id, "status": "Processing"}

@router.post("/api/v3/predict-intelligent")
@limiter.limit("100/minute")
def predict_intelligent(request: Request, req: PredictRequest):
    from orchestration.ensembles.router import DynamicEnsembleRouter
    features = req.model_dump(exclude={"model_name"}) if hasattr(req, "model_dump") else req.dict(exclude={"model_name"})
    try:
        res = DynamicEnsembleRouter.route_inference(features, strategy="fastest")
        return {"orchestration": "fastest", "prediction": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/scenarios")
@limiter.limit("20/minute")
def scenarios(request: Request, req: PredictRequest):
    features = req.model_dump(exclude={"model_name"}) if hasattr(req, "model_dump") else req.dict(exclude={"model_name"})
    return MLEngineService.analyze_scenarios(features)

@router.post("/api/forecast")
@limiter.limit("20/minute")
def forecast(request: Request, req: ForecastRequest):
    return MLEngineService.forecast_degradation(
        initial_capacity_kwh=req.initial_capacity_kwh,
        current_cycles=req.current_cycles,
        forecast_cycles=req.forecast_cycles,
        avg_temp_c=req.avg_temp_c,
    )

@router.get("/api/sample-data")
@limiter.limit("10/minute")
def sample_data(request: Request, n: int = 200):
    return MLEngineService.get_sample_data(n)

