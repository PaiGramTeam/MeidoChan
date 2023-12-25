import logging
from dataclasses import dataclass
from multiprocessing import RLock as Lock
from typing import Any, Mapping, Optional, TYPE_CHECKING

from typing_extensions import Self

from meido.utils.log import LoggerConfig
from meido.utils.typedefs import ArgsType, ExcInfoType

if TYPE_CHECKING:
    from multiprocessing.synchronize import RLock as LockType

logging.addLevelName(25, "SUCCESS")


class LoggerMeta(type):
    _lock: "LockType" = Lock()
    _instance: Optional["Logger"] = None

    def __call__(cls, *args, **kwargs) -> "Logger":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LoggerMeta, cls).__call__(*args, **kwargs)
            else:
                cls._instance.warning("A Logger instance already exists.")
        return cls._instance


@dataclass
class LoggerTracebackConfig:
    max_frames: int = 20
    trace_locals_max_depth: int | None = None
    trace_locals_max_length: int = 10
    trace_locals_max_string: int = 80


class Logger(logging.Logger, metaclass=LoggerMeta):
    """只能有一个实例的 Logger"""

    def __init__(
        self,
        name: str | None = None,
        level: str | int | None = None,
        *,
        config: LoggerConfig = LoggerConfig(),
    ):
        """Initialization Logger"""
        super().__init__(
            name or config.name or "arko-logger",
            logging.getLevelName(level or config.level or "INFO"),
        )
        self.handlers = []
        self.extras: dict[str, Any] | None = None
        self._config = config

    def opt(
        self,
        markup: bool | None = None,
        depth: int | None = None,
        keywords: list[str] | None = None,
        suppress: list[str] | None = None,
    ) -> Self:
        self.extras = {
            k: v
            for k, v in {
                "markup": markup,
                "depth": depth,
                "keywords": (keywords or []) + (self._config.keywords or []),
                "suppress": suppress,
            }.items()
            if v is not None
        }
        return self

    def _log(
        self,
        level: int,
        msg: object,
        args: ArgsType,
        exc_info: ExcInfoType | None = None,
        extra: Mapping[str, object] | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
    ) -> None:
        extra = self.extras | (extra or {})
        self.extras = None
        # noinspection PyProtectedMember
        return super()._log(level, msg, args, exc_info, extra, stack_info)

    def success(
        self,
        msg: object,
        *args: object,
        exc_info: ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        if self.isEnabledFor(25):
            self._log(
                25,
                msg,
                args,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra,
            )
