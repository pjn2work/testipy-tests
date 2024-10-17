from datetime import date, datetime, time, timedelta, timezone, tzinfo
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


class DatetimeCompare:
    def __init__(
            self,
            expected: datetime | date | str,
            dt_min: timedelta | None = None,
            dt_max: timedelta | None = None,
            *,
            dt_str_format: str = DATETIME_FORMAT_DEFAULT,
            expected_type: Literal["datetime", "date"] = "datetime",
            tz: tzinfo | str | None = None,
    ):
        self.tz = ZoneInfo(tz) if isinstance(tz, str) else tz
        self.expected_type = self._auto_detect_type(expected, expected_type)
        self.dt_str_format = dt_str_format
        self.expected = self._convert_to_datetime(expected)
        self.min_dt = dt_min or timedelta(0)
        self.max_dt = dt_max or timedelta(0)

    @staticmethod
    def _auto_detect_type(expected: datetime | date | str, expected_type: Literal["datetime", "date"]):
        if isinstance(expected, datetime):
            return "datetime"
        if isinstance(expected, date):
            return "date"
        if expected_type not in ("datetime", "date"):
            raise TypeError(f"Parameter expected_type is '{expected_type}'. Can only accept 'datetime' or 'date' strings")
        return expected_type

    def _convert_to_datetime(self, expected: datetime | date | str) -> datetime | date:
        if isinstance(expected, (datetime, date)):
            return expected
        if isinstance(expected, str):
            if self.expected_type == "datetime":
                _result = string_to_datetime(expected, format_=self.dt_str_format, tz=self.tz)
                return _result if self.tz is None or _result.tzinfo else _result.replace(tzinfo=self.tz)
            if self.expected_type == "date":
                return string_to_date(expected, format_=self.dt_str_format)
            raise TypeError(f"Unknown {self.expected_type=}!")
        raise TypeError(f"Expected {expected} is {type(expected)}. Can only accept objects that are datetime or date or string.")

    def __eq__(self, other):
        if isinstance(other, str):
            other = self._convert_to_datetime(other)

        if not isinstance(other, type(self.expected)):
            raise TypeError(f"Expected '{self.expected}' is {type(self.expected_type)}, but other '{other}' is {type(other)}")

        if isinstance(other, (datetime, date)):
            return self.expected - self.min_dt <= other <= self.expected + self.max_dt

        raise TypeError(f"Other '{other}' is {type(other)}. Can only accept datetime/date/str objects.")

    def __str__(self):
        return f"[{self.expected - self.min_dt} .. {self.expected + self.max_dt}]"

    __repr__ = __str__
