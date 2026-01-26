import logging.config
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def obfuscated(email: str, obfuscated_length: int) -> str:
    if "@" not in email:
        return email

    first, last = email.split("@")

    if len(first) <= obfuscated_length:
        return email

    visible_chars = first[:obfuscated_length]
    masked_count = len(first) - obfuscated_length
    return visible_chars + ("*" * masked_count) + "@" + last  # e.g em****@gmail.com


class EmailObfuscationFilter(logging.Filter):
    def __init__(self, name="", obfuscated_length: int = 2):
        super().__init__(name)
        self.obfuscated_length = obfuscated_length

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "email"):
            record.email = obfuscated(record.email, self.obfuscated_length)
        return True


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        result = super().format(record)
        record.levelname = levelname
        return result


def configure_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "email_obfuscation": {
                    "()": EmailObfuscationFilter,
                    "obfuscated_length": 3 if LOG_LEVEL == "DEBUG" else 2,
                },
            },
            "formatters": {
                "default": {
                    "()": ColoredFormatter,
                    "style": "{",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                    "format": "{asctime} {levelname:<8} [{name}:{lineno}] {message}",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "filters": ["email_obfuscation"],
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
