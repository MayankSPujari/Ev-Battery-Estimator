import os
from celery import Celery
from configs.config import settings

celery_app = Celery(
    "ev_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
)

@celery_app.task(name="predict_async")
def predict_async_task(features: dict, model_name: str):
    from backend.api.services import MLEngineService
    return MLEngineService.predict_range(features, model_name)
