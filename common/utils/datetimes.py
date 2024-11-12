from datetime import date, datetime, time, timedelta, timezone, tzinfo
from time import perf_counter
from typing import Literal
from zoneinfo import ZoneInfo

DATETIME_FORMAT_DEFAULT = "%Y-%m-%d %H:%M:%S"
DATETIME_FORMAT_ISO = "%Y-%m-%dT%H:%M:%S"
DATETIME_FORMAT_OFFSET = "%Y-%m-%dT%H:%M:%S%z"
DATE_FORMAT_ISO = "%Y-%m-%d"


def now() -> datetime:
    return datetime.now(timezone.utc)


def date_time_plus_timedelta(dt: datetime | date, /, **kwargs) -> datetime | date:
    return dt + timedelta(**kwargs)


def now_plus_timedelta(**kwargs) -> datetime:
    return date_time_plus_timedelta(now(), **kwargs)


def today() -> date:
    return now().date()


def yesterday() -> date:
    return now_plus_timedelta(days=-1).date()


def tomorrow() -> date:
    return now_plus_timedelta(days=1).date()


def midnight(date_: date, /) -> datetime:
    return datetime.combine(date=date_, time=time.min, tzinfo=timezone.utc)


def replace_timezone(datetime_: datetime, /, tz: tzinfo | str = timezone.utc) -> datetime:
    if isinstance(tz, str):
        tz = ZoneInfo(tz)
    return datetime_.replace(tzinfo=tz)


def change_timezone(datetime_: datetime, /, tz: tzinfo | str = timezone.utc) -> datetime:
    if isinstance(tz, str):
        tz = ZoneInfo(tz)
    return datetime_.astimezone(tz)


def isoformat_no_tz(datetime_: datetime, /, *, sep: Literal["T", " "] = "T") -> str:
    """2024-09-01T00:35:30"""
    return datetime_.strftime(f"%Y-%m-%d{sep}%H:%M:%S")


def isoformat_with_tz(datetime_: datetime, /, *, sep: Literal["T", " "] = "T") -> str:
    """2024-09-01T00:35:30Z"""
    return isoformat_no_tz(datetime_, sep=sep) + "Z"


def isoformat_with_offset(datetime_: datetime, /, *, sep: Literal["T", " "] = "T") -> str:
    """2024-09-01T00:35:30+01:00"""
    _as_str = datetime_.strftime(f"%Y-%m-%d{sep}%H:%M:%S%z")
    return _as_str[:-2] + ":" + _as_str[-2:]


def isoformat_with_zone(datetime_: datetime) -> str:
    """2024-09-01 00:35:30 WEST"""
    return datetime_.strftime(f"%Y-%m-%d %H:%M:%S %Z")


def isoformat_with_ms(datetime_: datetime, /, *, sep: Literal["T", " "] = " ") -> str:
    """2024-09-01 00:35:30.000"""
    return datetime_.strftime(f"%Y-%m-%d{sep}%H:%M:%S.%f")[:-3]


def isoformat_long(datetime_: datetime, /, *, sep: Literal["T", " "] = "T") -> str:
    """2024-09-01T00:35:30.000Z"""
    return isoformat_with_ms(datetime_, sep=sep) + "Z"


def string_to_datetime(datetime_: str, /, *, format_: str = DATETIME_FORMAT_DEFAULT, tz: tzinfo | str = timezone.utc) -> datetime:
    if isinstance(tz, str):
        tz = ZoneInfo(tz)
    _result = datetime.strptime(datetime_, format_)
    if tz is None:
        return _result
    else:
        if _result.tzinfo is None:
            return _result.replace(tzinfo=tz)
        else:
            return _result.astimezone(tz)


def string_to_date(date_: str, /, *, format_: str = DATE_FORMAT_ISO) -> date:
    return datetime.strptime(date_, format_).date()


def datetime_to_string(datetime_: datetime, /, format_: str = DATETIME_FORMAT_DEFAULT) -> str:
    return datetime_.strftime(format_)


def date_to_string(date_: date, /, format_: str = DATE_FORMAT_ISO) -> str:
    return date_.strftime(format_)


class DateCompare:
    def __init__(
            self,
            expected: date | str,
            dt_min: timedelta | None = None,
            dt_max: timedelta | None = None,
            /, *,
            dt_str_format: str | list[str] = DATE_FORMAT_ISO,
    ):
        self.dt_str_format: list[str] | str = dt_str_format if isinstance(dt_str_format, list) else [dt_str_format]
        self.expected = self._convert_to_date(expected)
        self.min_dt = dt_min or timedelta(0)
        self.max_dt = dt_max or timedelta(0)

    def _convert_to_date(self, date_value: date | str) -> date:
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, str):
            for dt_str_format in self.dt_str_format:
                try:
                    return string_to_date(date_value, format_=dt_str_format)
                except Exception:
                    pass
            raise ValueError(f"No format fit to decode '{date_value}")
        raise TypeError(f"Date {date_value} is {type(date_value)}. Can only accept objects that are date or string.")

    def __eq__(self, other):
        if isinstance(other, str):
            other = self._convert_to_date(other)
        return self.expected - self.min_dt <= other <= self.expected + self.max_dt

    def __str__(self):
        return f"[{self.expected - self.min_dt} .. {self.expected + self.max_dt}]"

    __repr__ = __str__


class DatetimeCompare:
    def __init__(
            self,
            expected: datetime | str,
            dt_min: timedelta | None = None,
            dt_max: timedelta | None = None,
            /, *,
            dt_str_format: str | list[str] = DATETIME_FORMAT_DEFAULT,
            tz: tzinfo | str | None = None,
    ):
        self.tz = ZoneInfo(tz) if isinstance(tz, str) else tz
        self.dt_str_format: list[str] | str = dt_str_format if isinstance(dt_str_format, list) else [dt_str_format]
        self.expected = self._convert_to_datetime(expected)
        self.min_dt = dt_min or timedelta(0)
        self.max_dt = dt_max or timedelta(0)

    def _convert_to_datetime(self, datetime_value: datetime | str) -> datetime:
        if isinstance(datetime_value, datetime):
            return datetime_value
        if isinstance(datetime_value, str):
            for dt_str_format in self.dt_str_format:
                try:
                    _result = string_to_datetime(datetime_value, format_=dt_str_format, tz=self.tz)
                    return _result if self.tz is None or _result.tzinfo else _result.replace(tzinfo=self.tz)
                except Exception:
                    pass
            raise ValueError(f"No format fit to decode '{datetime_value}")
        raise TypeError(f"Expected {datetime_value} is {type(datetime_value)}. Can only accept objects that are datetime or string.")

    def __eq__(self, other):
        if isinstance(other, str):
            other = self._convert_to_datetime(other)
        return self.expected - self.min_dt <= other <= self.expected + self.max_dt

    def __str__(self):
        return f"[{self.expected - self.min_dt} .. {self.expected + self.max_dt}]"

    __repr__ = __str__


class TimeIt:

    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = perf_counter()

    def millis(self) -> float:
        return (self.end - self.start) * 1000

    def seconds(self) -> float:
        return self.end - self.start

    def minutes(self) -> float:
        return (self.end - self.start) / 60

    def __str__(self):
        sec = self.seconds()
        # < 1 sec
        if sec < 1.000:
            return f"{sec*1000:.0f}ms"
        # < 10 sec
        if sec < 10.000:
            return f"{sec:.2f}s"

        hours = int(sec // 3600)
        minutes = int((sec % 3600) // 60)
        seconds = int(sec % 60)

        return f"{hours:0>2d}:{minutes:0>2d}:{seconds:0>2d}"
