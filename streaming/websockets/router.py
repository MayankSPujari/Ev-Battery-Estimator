import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ml.models.registry import ModelRegistry
from ml.utils import ml_logger

router = APIRouter()

@router.websocket("/ws/inference-stream")
async def inference_stream(websocket: WebSocket):
    await websocket.accept()
    reg = ModelRegistry.get_regressor()
    ml_logger.info("Client connected to real-time inference stream.")
    
    try:
        while True:
            data = await websocket.receive_json()
            # Expecting features and model_name in the stream payload
            features = data.get("features", {})
            model_name = data.get("model_name", "gradient_boosting")
            
            try:
                result = reg.predict(features, model_name)
                await websocket.send_json({"status": "success", "prediction": result})
            except Exception as e:
                await websocket.send_json({"status": "error", "detail": str(e)})
                
    except WebSocketDisconnect:
        ml_logger.info("Client disconnected from inference stream.")
