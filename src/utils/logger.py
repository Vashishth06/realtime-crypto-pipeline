import logging
import sys

from pathlib import Path

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with the specified name and level.

    Args:
        name (str): The name of the logger.
        level: The logging level (default: logging.INFO).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper())) # Converts "info" → logging.INFO

    # Create console handler and set level
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(getattr(logging, level.upper()))

    # Compute project root (go up from utils/ → src/ → root/)
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    # Create file handler and set level
    fh = logging.FileHandler(log_dir / f"{name}.log")
    fh.setLevel(getattr(logging, level.upper()))

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Add the handlers to the logger
    if not logger.hasHandlers():
        logger.addHandler(ch)
        logger.addHandler(fh)
    return logger
