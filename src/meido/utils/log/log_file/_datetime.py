from calendar import day_abbr, day_name, month_abbr, month_name
from datetime import datetime as datetime_, timedelta, timezone
from time import localtime, strftime

import regex as re

__all__ = (
    "aware_now",
    "FileDateFormatter",
)

tokens = r"H{1,2}|h{1,2}|m{1,2}|s{1,2}|S+|YYYY|YY|M{1,4}|D{1,4}|Z{1,2}|zz|A|X|x|E|Q|dddd|ddd|d"
pattern = re.compile(r"(?:{0})|\[(?:{0}|!UTC|)\]".format(tokens))  # skipcq: PYL-C0209


class FileDateFormatter:
    def __init__(self, _datetime: datetime_ | None = None) -> None:
        self.datetime = _datetime or aware_now()

    def __format__(self, spec: str) -> str:
        if not spec:
            spec = "%Y-%m-%d_%H-%M-%S_%f"
        return self.datetime.__format__(spec)


class Datetime(datetime_):  # noqa: N801
    def __format__(self, spec):
        if spec.endswith("!UTC"):
            dt = self.astimezone(timezone.utc)
            spec = spec[:-4]
        else:
            dt = self

        if not spec:
            spec = "%Y-%m-%dT%H:%M:%S.%f%z"

        if "%" in spec:
            return datetime_.__format__(dt, spec)

        if "SSSSSSS" in spec:
            raise ValueError(
                "Invalid time format: the provided format string contains more than six successive "
                "'S' characters. This may be due to an attempt to use nanosecond precision, which "
                "is not supported."
            )

        year, month, day, hour, minute, second, weekday, year_day, _ = dt.timetuple()
        microsecond = dt.microsecond
        timestamp = dt.timestamp()
        timezone_info = dt.tzinfo or timezone(timedelta(seconds=0))
        offset = timezone_info.utcoffset(dt).total_seconds()
        sign = ("-", "+")[offset >= 0]
        (h, m), s = divmod(abs(offset // 60), 60), abs(offset) % 60

        rep = {
            "YYYY": f"{year:04d}",
            "YY": f"{(year % 100):02d}",
            "Q": f"{((month - 1) // 3 + 1):0.0f}",
            "MMMM": month_name[month],
            "MMM": month_abbr[month],
            "MM": f"{month:02d}",
            "M": str(month),
            "DDDD": f"{year_day:03d}",
            "DDD": f"{year_day:d}",
            "DD": f"{day:02d}",
            "D": f"{day:d}",
            "dddd": day_name[weekday],
            "ddd": day_abbr[weekday],
            "d": f"{weekday:d}",
            "E": f"{(weekday + 1):d}",
            "HH": f"{hour:02d}",
            "H": f"{hour:d}",
            "hh": f"{((hour - 1) % 12 + 1):02d}",
            "h": f"{((hour - 1) % 12 + 1):d}",
            "mm": f"{minute:02d}",
            "m": f"{minute:d}",
            "ss": f"{second:02d}",
            "s": f"{second:d}",
            "S": f"{(microsecond // 100000):d}",
            "SS": f"{(microsecond // 10000):02d}",
            "SSS": f"{(microsecond // 1000):03d}",
            "SSSS": f"{(microsecond // 100):04d}",
            "SSSSS": f"{(microsecond // 10):05d}",
            "SSSSSS": f"{microsecond:06d}",
            "A": ("AM", "PM")[hour // 12],
            # "Z": "%s%02d:%02d%s" % (sign, h, m, f':{s:09.06f}'[: 11 if s % 1 else 3] * (s > 0)),
            "Z": f"{sign}{h:02d}:{m:02d}{f':{s:09.06f}'[: 11 if s % 1 else 3] * (s > 0)}",
            # "ZZ": "%s%02d%02d%s" % (sign, h, m, ("%09.06f" % s)[: 10 if s % 1 else 2] * (s > 0)),
            "ZZ": f"{sign}{h:02d}{m:02d}{f'{s:09.06f}'[: 10 if s % 1 else 2] * (s > 0)}",
            "zz": timezone_info.tzname(dt) or "",
            "X": f"{timestamp:d}",
            "x": f"{(int(timestamp) * 1000000 + microsecond):d}",
        }

        def get(_m):
            try:
                return rep[_m.group(0)]
            except KeyError:
                return _m.group(0)[1:-1]

        return pattern.sub(get, spec)


def aware_now() -> datetime_:
    now = datetime_.now()
    timestamp = now.timestamp()
    local = localtime(timestamp)

    try:
        seconds = local.tm_gmtoff
        zone = local.tm_zone
    except AttributeError:
        # Workaround for Python 3.5.
        utc_naive = datetime_.fromtimestamp(timestamp, tz=timezone.utc).replace(tzinfo=None)
        offset = datetime_.fromtimestamp(timestamp) - utc_naive
        seconds = offset.total_seconds()
        zone = strftime("%Z")

    timezone_info = timezone(timedelta(seconds=seconds), zone)

    return Datetime.combine(now.date(), now.time().replace(tzinfo=timezone_info))
