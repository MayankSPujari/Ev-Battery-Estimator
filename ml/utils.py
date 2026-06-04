import os
import logging

def get_logger(name: str) -> logging.Logger:
    """Configures and returns a centralized logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# Create a default logger for the ML package
ml_logger = get_logger("ml")
