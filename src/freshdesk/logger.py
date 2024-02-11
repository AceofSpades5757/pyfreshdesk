import logging
from pathlib import Path
from typing import Any


logs_path = Path(__file__).parent.parent / "logs"
logs_path.mkdir(exist_ok=True)
log_file = logs_path / Path(__file__).with_suffix(".log").name

LOGGING_CONFIG: dict[str, Any] = dict(
    version=1,
    disable_existing_loggers=False,
    root=dict(
        # level=logging.DEBUG, handlers=['stream_handler', 'file_handler']
        level=logging.DEBUG,
        handlers=["file_handler"],
    ),
    formatters={
        "default": {
            "date_format": "%Y-%m-%dT%H:%M:%S+0000%z",
            "format": "{asctime} - {name} - {levelname:<8} - {message}",
            "style": "{",
            "validate": True,
        }
    },
    handlers={
        # 'stream_handler': {
        # 'level': logging.DEBUG,
        # 'class': 'logging.StreamHandler',
        # 'formatter': 'default',
        # },
        "file_handler": {
            "level": logging.DEBUG,
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": log_file,
        },
    },
    loggers={},
)


def get_config(filename: str) -> dict[str, Any]:
    log_file = logs_path / Path(filename).with_suffix(".log").name
    LOGGING_CONFIG["handlers"]["file_handler"]["filename"] = log_file
    return LOGGING_CONFIG
