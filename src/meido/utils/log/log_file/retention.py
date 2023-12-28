import datetime
import os
from collections.abc import Callable
from functools import partial

from meido.utils.log import _parsers as string_parsers

__all__ = ("Retention",)


def preprocess_string(string: str) -> datetime.timedelta:
    if (interval := string_parsers.parse_duration(string)) is None:
        raise ValueError("Cannot parse retention from: '%s'" % string)
    return interval


class Retention:
    _retention: Callable

    def __init__(self, retention: str | datetime.timedelta | Callable | None) -> None:
        if isinstance(retention, str):
            retention = preprocess_string(retention)

        if isinstance(retention, datetime.timedelta):
            self._retention = partial(Retention.retention_age, seconds=retention.total_seconds())
        elif isinstance(retention, int):
            self._retention = partial(Retention.retention_count, number=retention)
        elif callable(retention):
            self._retention = retention
        else:
            raise TypeError("Cannot infer retention for objects of type: '%s'" % type(retention).__name__)

    def __call__(self, *args, **kwargs):
        # noinspection PyCallingNonCallable
        return self._retention(*args, **kwargs)

    @staticmethod
    def retention_count(logs, number):
        def key_log(_log):
            return -os.stat(_log).st_mtime, _log

        for log in sorted(logs, key=key_log)[number:]:
            os.remove(log)

    @staticmethod
    def retention_age(logs, seconds):
        t = datetime.datetime.now().timestamp()
        for log in logs:
            if os.stat(log).st_mtime <= t - seconds:
                os.remove(log)
