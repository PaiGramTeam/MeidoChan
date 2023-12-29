import datetime
import glob
import os
import string
from collections.abc import Callable
from pathlib import Path
from stat import ST_DEV, ST_INO
from types import TracebackType
from typing import AnyStr, IO, Iterable, Iterator, Optional

from meido.utils.log._ctime import get_ctime, set_ctime
from meido.utils.log.log_file._datetime import FileDateFormatter
from meido.utils.log.log_file._path import generate_rename_path
from meido.utils.log.log_file.compression import Compression
from meido.utils.log.log_file.retention import Retention
from meido.utils.log.log_file.rotation import Rotation


def _make_glob_patterns(path: Path) -> list[str]:
    formatter = string.Formatter()
    tokens = formatter.parse(str(path))
    escaped = "".join(glob.escape(text) + "*" * (name is not None) for text, name, *_ in tokens)

    root, ext = os.path.splitext(escaped)

    if not ext:
        return [escaped, escaped + ".*"]

    return [escaped, escaped + ".*", root + ".*" + ext, root + ".*" + ext + ".*"]


class LogFile(IO[str]):
    """日志文件类"""

    def _create_path(self) -> Path:
        path = str(self._path).format_map({"time": FileDateFormatter()})
        return Path(path).resolve()

    @staticmethod
    def _create_dirs(path: str | Path) -> None:
        dirname = os.path.dirname(path)
        os.makedirs(dirname, exist_ok=True)

    def _create_file(self, path: str | Path) -> None:
        self._file = open(path, **self._kwargs)
        self._file_path = path

    def __init__(
        self,
        path: str | Path,
        *,
        rotation: str | int | datetime.time | datetime.timedelta | Callable | None = None,
        retention: str | int | datetime.timedelta | Callable | None = None,
        compression: str | Callable | None = None,
        **kwargs,
    ) -> None:
        self._path = Path(path).resolve()
        self._kwargs = kwargs | {"encoding": "utf-8", "mode": "a", "buffering": 1}

        self._glob_patterns = _make_glob_patterns(self._path)
        self._rotation_function = Rotation(rotation)
        self._retention_function = Retention(retention)
        self._compression_function = Compression(compression)

        self._file = None
        self._file_path = None

        self._file_dev = -1
        self._file_ino = -1

        path = self._create_path()
        self._create_dirs(path)
        self._create_file(path)

    def _close_file(self):
        if self._file is not None:
            self._file.flush()
            self._file.close()

            self._file = None
            self._file_path = None
            self._file_dev = -1
            self._file_ino = -1

    def _reopen_if_needed(self) -> None:
        """按需打开"""
        if not self._file:
            return

        filepath = self._file_path

        try:
            result = os.stat(filepath)
        except FileNotFoundError:
            result = None

        if not result or result[ST_DEV] != self._file_dev or result[ST_INO] != self._file_ino:
            self._close_file()
            self._create_dirs(filepath)
            self._create_file(filepath)

    def _terminate_file(self, *, is_rotating: bool = False) -> None:
        """关闭文件"""
        self._close_file()

        old_path = self._file_path

        new_path = None

        if is_rotating:
            new_path = self._create_path()
            self._create_dirs(new_path)

            if new_path == old_path:
                creation_time = get_ctime(old_path)
                root, ext = os.path.splitext(old_path)
                renamed_path = generate_rename_path(root, ext, creation_time)
                os.rename(old_path, renamed_path)
                old_path = renamed_path

        if is_rotating or self._rotation_function is None:
            if self._compression_function is not None and old_path is not None:
                self._compression_function(old_path)

            if self._retention_function is not None:
                logs = {file for pattern in self._glob_patterns for file in glob.glob(pattern) if os.path.isfile(file)}
                self._retention_function(list(logs))

        if is_rotating:
            self._create_file(new_path)
            set_ctime(new_path, datetime.datetime.now().timestamp())

    def _get_file(self) -> IO[str]:
        if self._file is None:
            path = self._create_path()
            self._create_dirs(path)
            self._create_file(path)

        return self._file

    def write(self, s: AnyStr) -> int:
        if self._file is None:
            path = self._create_path()
            self._create_dirs(path)
            self._create_file(path)

        self._reopen_if_needed()

        if self._rotation_function is not None and self._rotation_function(s, self._file):
            self._terminate_file(is_rotating=True)

        return self._file.write(s)

    def close(self) -> None:
        self._reopen_if_needed()
        self._terminate_file(is_rotating=False)

    def fileno(self) -> int:
        return self._file.fileno()

    def flush(self) -> None:
        return self._file.flush()

    def isatty(self) -> bool:
        return self._file.isatty()

    def read(self, n: int = -1) -> AnyStr:
        return self._file.read(n)

    def readable(self) -> bool:
        return self._file.readable()

    def readline(self, limit: int = ...) -> AnyStr:
        return self._file.readline()

    # noinspection SpellCheckingInspection
    def readlines(self, hint: int = ...) -> list[AnyStr]:
        return self._file.readlines()

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._file.seek(offset, whence)

    def seekable(self) -> bool:
        return self._file.seekable()

    def tell(self) -> int:
        return self._file.tell()

    def truncate(self, size: Optional[int] = None) -> int:
        return self._file.truncate(size)

    def writable(self) -> bool:
        return self._file.writable()

    def writelines(self, lines: Iterable[AnyStr]) -> None:
        return self._file.writelines(lines)

    def __next__(self) -> AnyStr:
        return self._file.__next__()

    def __iter__(self) -> Iterator[AnyStr]:
        return self._file.__iter__()

    def __enter__(self) -> IO[AnyStr]:
        return self._file.__enter__()

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        exception_traceback: TracebackType | None,
    ) -> None:
        return self._file.__exit__(exception_type, exception, exception_traceback)