import time
from fastapi import Request
from ml.utils import ml_logger

async def timing_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    ml_logger.info(f"{request.method} {request.url.path} - {process_time:.4f}s")
    return response
