import datetime
import os
from collections.abc import Callable
from decimal import Decimal
from functools import partial
from numbers import Real

from meido.utils.log import _parsers as string_parsers
from meido.utils.log.log_file._ctime import get_ctime, set_ctime

__all__ = ("Rotation",)


def preprocess_string(string: str) -> float | int | tuple[int, datetime.time] | None:
    if (size := string_parsers.parse_size(string)) is not None:
        return size

    if (interval := string_parsers.parse_duration(string)) is not None:
        return interval

    if (frequency := string_parsers.parse_frequency(string)) is not None:
        return frequency

    if (daytime := string_parsers.parse_daytime(string)) is not None:
        day, time = daytime
        if day is None:
            return time
        return daytime

    raise ValueError(f"Cannot parse rotation from: '{string}'")


class Rotation:
    _rotation: Callable

    def __init__(self, rotation: str | int | datetime.time | datetime.timedelta | Callable | None) -> None:
        if isinstance(rotation, str):
            rotation = preprocess_string(rotation)

        if isinstance(rotation, tuple):
            day, time = rotation
            if time is None:
                time = datetime.time(0, 0, 0)
            step_forward = partial(Rotation.forward_weekday, weekday=day)
            self._rotation = Rotation.RotationTime(step_forward, time)
        elif isinstance(rotation, (Real, Decimal)):
            self._rotation = partial(Rotation.rotation_size, size_limit=rotation)
        elif isinstance(rotation, datetime.time):
            self._rotation = Rotation.RotationTime(Rotation.forward_day, rotation)
        elif isinstance(rotation, datetime.timedelta):
            step_forward = partial(Rotation.forward_interval, interval=rotation)
            self._rotation = Rotation.RotationTime(step_forward)
        elif callable(rotation):
            self._rotation = rotation
        else:
            raise TypeError(f"Cannot infer rotation for objects of type: '{type(rotation).__name__}'")

    def __call__(self, *args, **kwargs):
        return self._rotation(*args, **kwargs)

    @staticmethod
    def forward_day(t):
        return t + datetime.timedelta(days=1)

    @staticmethod
    def forward_weekday(t, weekday):
        while True:
            t += datetime.timedelta(days=1)
            if t.weekday() == weekday:
                return t

    @staticmethod
    def forward_interval(t, interval):
        return t + interval

    @staticmethod
    def rotation_size(message, file, size_limit):
        file.seek(0, 2)
        return file.tell() + len(message) > size_limit

    class RotationTime:
        def __init__(self, step_forward, time_init=None):
            self._step_forward = step_forward
            self._time_init = time_init
            self._limit = None

        def _update_limit(self, record_time, file):
            if self._limit is None:
                filepath = os.path.realpath(file.name)
                creation_time = get_ctime(filepath)
                set_ctime(filepath, creation_time)
                start_time = datetime.datetime.fromtimestamp(creation_time, tz=datetime.timezone.utc)

                time_init = self._time_init

                if time_init is None:
                    limit = start_time.astimezone(record_time.tzinfo).replace(tzinfo=None)
                    limit = self._step_forward(limit)
                else:
                    timezone_info = record_time.tzinfo if time_init.tzinfo is None else time_init.tzinfo
                    limit = start_time.astimezone(timezone_info).replace(
                        hour=time_init.hour,
                        minute=time_init.minute,
                        second=time_init.second,
                        microsecond=time_init.microsecond,
                    )

                    if limit <= start_time:
                        limit = self._step_forward(limit)

                    if time_init.tzinfo is None:
                        limit = limit.replace(tzinfo=None)

                self._limit = limit

        def __call__(self, message, file) -> bool:
            record_time = message.record["time"]

            self._update_limit(record_time, file)

            if self._limit.tzinfo is None:
                record_time = record_time.replace(tzinfo=None)

            if record_time >= self._limit:
                while self._limit <= record_time:
                    self._limit = self._step_forward(self._limit)
                return True
            return False
