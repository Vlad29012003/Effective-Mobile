import inspect
import logging
import logging.config
import sys
from collections.abc import Callable
from typing import Any, TextIO

from loguru import logger

_INFO_PREFIXES = (
    "botocore.",
    "boto3.",
    "s3transfer.",
    "urllib3.",
    "django.",
)

_INFO_LEVEL_NO = logger.level("INFO").no
_DEBUG_LEVEL_NO = logger.level("DEBUG").no


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename

            if depth > 0 and not (is_logging or is_frozen):
                break

            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def default_filter(record: dict[str, Any]) -> bool:
    name = record.get("name", "")
    level_no = record["level"].no

    if name.startswith(_INFO_PREFIXES):
        return level_no >= _INFO_LEVEL_NO

    return level_no >= _DEBUG_LEVEL_NO


def configure_logging(
    config_dict: dict[str, Any],
    *,
    intercept_root: bool = True,
    filter_fn: Callable[[dict[str, Any]], bool] = default_filter,
    sink: TextIO = sys.stderr,
    loguru_level: str = "DEBUG",
) -> None:
    logging.config.dictConfig(config_dict)

    if intercept_root:
        root = logging.getLogger()
        root.handlers = [InterceptHandler()]
        root.setLevel(logging.NOTSET)

    logger.remove()
    logger.add(sink, level=loguru_level, filter=filter_fn) # type: ignore[arg-type]
