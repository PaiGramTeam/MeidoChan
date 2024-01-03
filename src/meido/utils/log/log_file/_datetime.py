from calendar import day_abbr, day_name, month_abbr, month_name
from datetime import datetime as datetime_, timedelta, timezone
from time import localtime, strftime

import regex as re

__all__ = (
    "aware_now",
    "FileDateFormatter",
)

tokens = r"H{1,2}|h{1,2}|m{1,2}|s{1,2}|S+|YYYY|YY|M{1,4}|D{1,4}|Z{1,2}|zz|A|X|x|E|Q|dddd|ddd|d"
pattern = re.compile(r"(?:{0})|\[(?:{0}|!UTC|)\]".format(tokens))


class FileDateFormatter:
    def __init__(self, _datetime: datetime_ | None = None) -> None:
        self.datetime = _datetime or aware_now()

    def __format__(self, spec: str) -> str:
        if not spec:
            spec = "%Y-%m-%d_%H-%M-%S_%f"
        return self.datetime.__format__(spec)


class Datetime(datetime_):  # noqa: N801
    def __format__(self, spec):  # skipcq: PYL-C0209
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
            "YYYY": "%04d" % year,
            "YY": "%02d" % (year % 100),
            "Q": "%d" % ((month - 1) // 3 + 1),
            "MMMM": month_name[month],
            "MMM": month_abbr[month],
            "MM": "%02d" % month,
            "M": "%d" % month,
            "DDDD": "%03d" % year_day,
            "DDD": "%d" % year_day,
            "DD": "%02d" % day,
            "D": "%d" % day,
            "dddd": day_name[weekday],
            "ddd": day_abbr[weekday],
            "d": "%d" % weekday,
            "E": "%d" % (weekday + 1),
            "HH": "%02d" % hour,
            "H": "%d" % hour,
            "hh": "%02d" % ((hour - 1) % 12 + 1),
            "h": "%d" % ((hour - 1) % 12 + 1),
            "mm": "%02d" % minute,
            "m": "%d" % minute,
            "ss": "%02d" % second,
            "s": "%d" % second,
            "S": "%d" % (microsecond // 100000),
            "SS": "%02d" % (microsecond // 10000),
            "SSS": "%03d" % (microsecond // 1000),
            "SSSS": "%04d" % (microsecond // 100),
            "SSSSS": "%05d" % (microsecond // 10),
            "SSSSSS": "%06d" % microsecond,
            "A": ("AM", "PM")[hour // 12],
            "Z": "%s%02d:%02d%s" % (sign, h, m, (":%09.06f" % s)[: 11 if s % 1 else 3] * (s > 0)),
            "ZZ": "%s%02d%02d%s" % (sign, h, m, ("%09.06f" % s)[: 10 if s % 1 else 2] * (s > 0)),
            "zz": timezone_info.tzname(dt) or "",
            "X": "%d" % timestamp,
            "x": "%d" % (int(timestamp) * 1000000 + microsecond),
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
