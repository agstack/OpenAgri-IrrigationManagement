import logging.config
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def configure_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "style": "{",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                    "format": "{asctime} {levelname:<8} [{name}:{lineno}] {message}",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": LOG_LEVEL,
                },
            },
            "root": {
                "handlers": ["console"],
                "level": LOG_LEVEL,
            },
            "loggers": {
                "api": {
                    "handlers": ["console"],
                    "level": LOG_LEVEL,
                    "propagate": False,
                },
                "uvicorn": {
                    "handlers": ["console"],
                    "level": "WARNING",
                    "propagate": False,
                },
                "python_multipart": {
                    "level": "WARNING",
                    "propagate": False,
                },
            },
        }
    )
