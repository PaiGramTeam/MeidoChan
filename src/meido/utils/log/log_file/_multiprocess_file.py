import datetime
import multiprocessing
import sys
from io import StringIO
from multiprocessing import Queue, Value
from pathlib import Path
from types import TracebackType
from typing import Any, AnyStr, Callable, IO, Mapping

from meido.utils.log.log_file._file import LogFile

if sys.platform != "win32":
    from multiprocessing.popen_spawn_posix import Popen as _BasePopen
else:
    from multiprocessing.popen_spawn_win32 import Popen as _BasePopen

__all__ = ("MultiProcessFile",)


class Popen(_BasePopen):
    def __init__(self, process_obj: "Process"):
        self._fds = []
        self._signal = process_obj.signal
        super().__init__(process_obj)

    if sys.platform == "win32":
        # noinspection PyProtectedMember
        def wait(self, timeout: float | None = None) -> int | None:
            import _winapi
            import signal

            from multiprocessing.popen_spawn_win32 import TERMINATE

            if self.returncode is None:
                if timeout is None:
                    msecs = _winapi.INFINITE
                else:
                    msecs = max(0, int(timeout * 1000 + 0.5))

                try:
                    res = _winapi.WaitForSingleObject(int(self._handle), msecs)
                except KeyboardInterrupt:
                    res = None
                if res == _winapi.WAIT_OBJECT_0:
                    code = _winapi.GetExitCodeProcess(self._handle)
                    if code == TERMINATE:
                        code = -signal.SIGTERM
                    self.returncode = code

            return self.returncode

    # noinspection PyProtectedMember
    def _terminate_win32(self):
        import _winapi
        from multiprocessing.popen_spawn_win32 import TERMINATE

        if self.returncode is None:
            try:
                # noinspection PyUnresolvedReferences
                _winapi.TerminateProcess(int(self._handle), TERMINATE)
            except OSError:
                if self.wait(timeout=1.0) is None:
                    raise

    def terminate(self):
        self._signal.value = False
        self.wait()
        if sys.platform != "win32":
            super().terminate()
        else:
            self._terminate_win32()


class Process(multiprocessing.Process):
    _signal: Value

    @property
    def signal(self) -> multiprocessing.Value:
        return self._signal

    def __init__(self, queue: Queue, signal: multiprocessing.Value, kwargs: Mapping[str, Any]) -> None:
        self._signal = signal
        self._queue = queue
        super().__init__(None, None, None, (), kwargs, daemon=True)

    @staticmethod
    def _Popen(process_obj: "Process"):
        return Popen(process_obj)

    def run(self):
        file = LogFile(**self._kwargs)

        def print_to_file():
            while not self._queue.empty():
                string = self._queue.get()
                file.write(string)

        while self.signal.value:
            if self._queue.empty():
                continue
            print_to_file()

        print_to_file()
        file.close()


class MultiProcessFile(StringIO):
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
        self._signal: Value = Value("i", 1)
        self._process = Process(self._queue, self._signal, self._kwargs)
        self._process.start()

    def _get_file(self) -> IO[str]:
        return self._file

    def write(self, s: AnyStr) -> int:
        self._queue.put(s)
        return len(s)

    def close(self) -> None:
        self._signal.value = False
        if self._process.is_alive():
            self._process.close()

    def flush(self) -> None:
        return self._file.flush()

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        exception_traceback: TracebackType | None,
    ) -> None:
        self.close()
        return self._get_file().__exit__(exception_type, exception, exception_traceback)

    def __del__(self) -> None:
        self.close()
