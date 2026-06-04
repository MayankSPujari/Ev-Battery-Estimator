from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import onnx
import os
from ml.utils import ml_logger

def convert_to_onnx(model, model_name: str, num_features: int, output_dir: str):
    """Converts a Scikit-Learn model to ONNX for hardware acceleration."""
    initial_type = [('float_input', FloatTensorType([None, num_features]))]
    onx = convert_sklearn(model, initial_types=initial_type)
    
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{model_name}.onnx")
    with open(path, "wb") as f:
        f.write(onx.SerializeToString())
    ml_logger.info(f"ONNX Model saved to {path}")
    return path
