import sys
from loguru import logger
import json


def setup_logging():
    # Remove default logger
    logger.remove()

    # Add a stdout logger with standard readable format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )

    # Add a JSON logger for ELK (Logstash/Fluentd)
    logger.add(
        "logs/app.log",
        format="{message}",
        serialize=True,  # This makes loguru output as JSON automatically
        rotation="100 MB",
        retention="30 days",
        level="INFO",
    )


setup_logging()
