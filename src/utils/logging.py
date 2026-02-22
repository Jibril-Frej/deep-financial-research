"""Logging utility for the Deep Financial Research project."""

import logging
import sys
from pathlib import Path


def setup_logger(name: str = "financial_research"):
    """Configures a logger with a clean format for console and file."""

    logger = logging.getLogger(name)

    # If logger already has handlers, don't add more (prevents duplicate logs)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # 1. Define the Format
    # Includes: Timestamp | Level | Module:Line | Message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 2. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 3. File Handler (Optional but helpful for Deep Research)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "research.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Create a singleton instance
logger = setup_logger()
