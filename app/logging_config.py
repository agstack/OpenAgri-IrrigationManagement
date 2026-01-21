import os
from logging.config import dictConfig


def configure_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(asctime)s.%(msecs)03dZ %(levelname)-8s [%(name)s:%(lineno)d] - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "console",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "handlers": ["default"],
                "level": log_level,
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default"],
                    "level": "INFO",
                    "propagate": False
                },
                "app": {
                    "handlers": ["default"],
                    "level": log_level,
                    "propagate": False,
                },
                "database": {
                    "handlers": ["default"],
                    "level": "WARNING",
                    "propagate": False
                },
            },
        }
    )