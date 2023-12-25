from types import TracebackType
from typing import AnyStr, IO, Iterable, Iterator


class HandlerIO(IO[str]):
    def close(self) -> None:
        ...

    @property
    def closed(self) -> bool:
        ...

    def fileno(self) -> int:
        ...

    def flush(self) -> None:
        ...

    def isatty(self) -> bool:
        ...

    def read(self, __n: int = -1) -> AnyStr:
        ...

    def readable(self) -> bool:
        ...

    def readline(self, __limit: int = -1) -> AnyStr:
        ...

    def readlines(self, __hint: int = -1) -> list[AnyStr]:
        ...

    def seek(self, __offset: int, __whence: int = 0) -> int:
        ...

    def seekable(self) -> bool:
        ...

    def tell(self) -> int:
        ...

    def truncate(self, __size: int | None = None) -> int:
        ...

    def writable(self) -> bool:
        ...

    def write(self, __s: AnyStr) -> int:
        ...

    def writelines(self, __lines: Iterable[AnyStr]) -> None:
        ...

    def __next__(self) -> AnyStr:
        ...

    def __iter__(self) -> Iterator[AnyStr]:
        ...

    def __enter__(self) -> IO[AnyStr]:
        ...

    def __exit__(
        self,
        __type: type[BaseException] | None,
        __value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> None:
        ...
