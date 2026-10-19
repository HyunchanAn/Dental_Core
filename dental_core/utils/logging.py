import logging
import sys


def get_logger(name: str = "dental_core", level: int = logging.INFO) -> logging.Logger:
    """
    Creates or retrieves a configured logger with a consistent timestamped format
    across Dental AI pipeline modules.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    return logger
