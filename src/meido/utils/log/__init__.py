from functools import lru_cache
from typing import TYPE_CHECKING

import regex as re

from meido.config import config
from meido.utils.const import PROJECT_ROOT
from meido.utils.log._config import LoggerConfig
from meido.utils.log._handler import Handler
from meido.utils.log._logger import Logger

if TYPE_CHECKING:
    from logging import LogRecord

__all__ = ("logger",)

logger_config = LoggerConfig(
    name=config.logger.name,
    level="DEBUG" if config.debug else "INFO",
    width=config.logger.width,
    keywords=config.logger.keywords,
    time_format=config.logger.time_format,
    capture_warnings=config.logger.capture_warnings,
    log_path=config.logger.path,
    project_root=PROJECT_ROOT,
    traceback=config.logger.traceback,
)
logger = Logger()


@lru_cache
def _whitelist_name_filter(record_name: str) -> bool:
    """白名单过滤器"""
    return any(re.match(rf"^{name}.*?$", record_name) for name in config.logger.filtered_names + [config.logger.name])


def name_filter(record: "LogRecord") -> bool:
    """默认的过滤器. 白名单

    根据当前的 record 的 name 判断是否需要打印。如果应该打印，则返回 True;否则返回 False。
    """
    return _whitelist_name_filter(record.name)
