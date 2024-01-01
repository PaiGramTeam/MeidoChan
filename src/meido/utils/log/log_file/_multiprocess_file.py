import datetime
from multiprocessing import Event, Process
from multiprocessing.queues import Queue
from multiprocessing.synchronize import Event as EventType
from pathlib import Path
from types import TracebackType
from typing import AnyStr, Callable, IO, Iterable, Iterator

from meido.utils.log.log_file._file import LogFile

__all__ = ("MultiProcessFile", )


def _process(queue: Queue, event: EventType, file: LogFile) -> None:
    while event.is_set():
        if queue.empty():
            continue
        string = queue.get()
        file.write(string)
    file.close()


class MultiProcessFile(IO[str]):
    def __init__(
        self,
        path: str | Path,
        *,
        rotation: str | int | datetime.time | datetime.timedelta | Callable | None = None,
        retention: str | int | datetime.timedelta | Callable | None = None,
        compression: str | Callable | None = None,
        **kwargs,
    ) -> None:
        self._kwargs = {
            "path": path,
            "rotation": rotation,
            "retention": retention,
            "compression": compression,
            **kwargs,
        }
        self._queue = Queue()
        self._file = LogFile(**self._kwargs)
        self._event: EventType = Event()
        self._event.set()
        self._process = Process(target=_process, args=(self._queue, self._event, self._file))

    def _get_file(self) -> IO[str]:
        return self._file

    def write(self, s: AnyStr) -> int:
        self._queue.put(s)
        return len(s)

    def close(self) -> None:
        self._event.clear()

    def fileno(self) -> int:
        return self._get_file().fileno()

    def flush(self) -> None:
        return self._get_file().flush()

    def isatty(self) -> bool:
        return self._get_file().isatty()

    def read(self, n: int = -1) -> AnyStr:
        return self._get_file().read(n)

    def readable(self) -> bool:
        return self._get_file().readable()

    def readline(self, limit: int = ...) -> AnyStr:
        return self._get_file().readline()

    # noinspection SpellCheckingInspection
    def readlines(self, hint: int = ...) -> list[AnyStr]:
        return self._get_file().readlines()

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._get_file().seek(offset, whence)

    def seekable(self) -> bool:
        return self._get_file().seekable()

    def tell(self) -> int:
        return self._get_file().tell()

    def truncate(self, size: int | None = None) -> int:
        return self._get_file().truncate(size)

    def writable(self) -> bool:
        return self._get_file().writable()

    def writelines(self, lines: Iterable[AnyStr]) -> None:
        return self._get_file().writelines(lines)

    def __next__(self) -> AnyStr:
        return self._get_file().__next__()

    def __iter__(self) -> Iterator[AnyStr]:
        return self._get_file().__iter__()

    def __enter__(self) -> IO[AnyStr]:
        return self._get_file().__enter__()

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        exception_traceback: TracebackType | None,
    ) -> None:
        return self._get_file().__exit__(exception_type, exception, exception_traceback)
