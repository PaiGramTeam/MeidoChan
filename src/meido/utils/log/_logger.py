import logging
import os
from inspect import currentframe
from io import StringIO
from multiprocessing import RLock as Lock
from sys import exc_info as get_exc_info
from traceback import print_stack
from types import FrameType
from typing import Any, Mapping, Optional, TYPE_CHECKING

from typing_extensions import Self

from meido.utils.log._config import LoggerConfig
from meido.utils.log._handler import Handler
from meido.utils.typedefs import ArgsType, ExcInfoType

from meido.utils.log.log_file import LogFile, MultiProcessFile

if TYPE_CHECKING:
    from multiprocessing.synchronize import RLock as LockType

__all__ = ("Logger",)


logging.addLevelName(25, "SUCCESS")

_srcfile = os.path.normcase(__file__)


def _is_internal_frame(frame: FrameType) -> bool:
    filename = os.path.normcase(frame.f_code.co_filename)
    return (
        filename == _srcfile
        or ("importlib" in filename and "_bootstrap" in filename)
        or logging._is_internal_frame(frame)
    )


class LoggerMeta(type):
    _lock: "LockType" = Lock()
    _instance: Optional["Logger"] = None

    def __call__(cls, *args, **kwargs) -> "Logger":
        with cls._lock:
            cls._instance = super(LoggerMeta, cls).__call__(*args, **kwargs)
        return cls._instance


class Logger(logging.Logger, metaclass=LoggerMeta):  # skipcq: PY-A6006
    """只能有一个实例的 Logger"""

    def __init__(
        self,
        name: str | None = None,
        level: str | int = 0,
        *,
        config: LoggerConfig = LoggerConfig(),
    ):
        """Initialization Logger"""
        super().__init__(
            name or config.name or "meido-logger",
            logging.getLevelName(level or config.level or "INFO"),
        )
        self.handlers = []
        self._extras: dict[str, Any] = {}
        self._config = config
        self.addHandler(
            Handler(
                level,
                width=config.width,
                color_system=config.color_system,
                omit_repeated_times=config.omit_repeated_times,
                project_root=config.project_root,
                time_format=config.time_format,
                traceback_configs=config.traceback,
            )
        )
        # Debug log
        self.addHandler(
            Handler(
                "DEBUG",
                file=(MultiProcessFile if config.multiprocess else LogFile)("log/debug/debug.log"),
                width=120,
                omit_repeated_times=True,
                project_root=config.project_root,
                time_format=config.time_format,
                traceback_configs=config.traceback,
            )
        )
        # Error log
        self.addHandler(
            Handler(
                "ERROR",
                file=(MultiProcessFile if config.multiprocess else LogFile)("log/error/error.log"),
                width=120,
                omit_repeated_times=True,
                project_root=config.project_root,
                time_format=config.time_format,
                traceback_configs=config.traceback,
            )
        )

    def opt(
        self,
        markup: bool | None = None,
        depth: int | None = None,
        keywords: list[str] | None = None,
        suppress: list[str] | None = None,
    ) -> Self:
        self._extras = {
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
        extra: Mapping[str, Any] | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
    ) -> None:
        extra = self._extras | (extra or {})
        self._extras = {}
        sinfo = None
        try:
            fn, lno, func, sinfo = self.findCaller(stack_info, stacklevel)
        except ValueError:  # pragma: no cover
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        if exc_info:
            if isinstance(exc_info, BaseException):
                exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif not isinstance(exc_info, tuple):
                exc_info = get_exc_info()
        self.handle(self.makeRecord(self.name, level, fn, lno, msg, args, exc_info, func, extra, sinfo))

    def findCaller(self, stack_info: bool = False, stacklevel: int = 1) -> tuple[str, int, str, str | None]:
        if (f := currentframe()) is None:
            return "(unknown file)", 0, "(unknown function)", None
        while stacklevel > 0:
            if (next_f := f.f_back) is None:
                break
            f = next_f
            if not _is_internal_frame(f):
                stacklevel -= 1
        co = f.f_code
        sinfo = None
        if stack_info:
            with StringIO() as sio:
                sio.write("Stack (most recent call last):\n")
                print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == "\n":
                    sinfo = sinfo[:-1]
        return co.co_filename, f.f_lineno, co.co_name, sinfo

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
