import time
import threading
from ml.utils import ml_logger

class ChaosSimulator:
    """Injects chaos engineering anomalies to validate platform resilience."""
    
    @staticmethod
    def inject_latency(max_latency_ms: int = 5000):
        ml_logger.warning(f"CHAOS: Injecting {max_latency_ms}ms latency.")
        time.sleep(max_latency_ms / 1000.0)
        
    @staticmethod
    def terminate_worker_thread():
        ml_logger.critical("CHAOS: Terminating active worker thread.")
        raise SystemExit("Chaos monkey killed the worker.")
