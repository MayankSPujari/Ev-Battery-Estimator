from ml.models.registry import ModelRegistry
from ml.utils import ml_logger

class DynamicEnsembleRouter:
    """Intelligent inference router that dynamically selects the best model."""
    
    @staticmethod
    def route_inference(features: dict, strategy: str = "fastest") -> dict:
        """
        Routes the inference request to the optimal model based on the strategy.
        In a real global mesh, this evaluates live metrics (latency, drift) to route.
        """
        reg = ModelRegistry.get_regressor()
        
        if strategy == "fastest":
            # Assume Ridge is fastest
            ml_logger.info("Routing to Ridge (Fastest Strategy)")
            return reg.predict(features, "ridge_poly")
        elif strategy == "most_accurate":
            # Assume Gradient Boosting is most accurate
            ml_logger.info("Routing to GB (Most Accurate Strategy)")
            return reg.predict(features, "gradient_boosting")
        elif strategy == "ensemble":
            ml_logger.info("Generating full ensemble consensus")
            return reg.predict_all(features)
        
        raise ValueError("Invalid orchestration strategy")
