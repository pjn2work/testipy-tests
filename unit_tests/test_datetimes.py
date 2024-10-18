import pytest

from common.utils.datetimes import *


expected_as_str_tz = "2024-08-09T10:00:30+00:00"
expected_as_str = "2024-07-31 17:00:30"

expected_as_datetime_tz: datetime = datetime.fromisoformat(expected_as_str_tz)
expected_as_datetime: datetime = datetime.fromisoformat(expected_as_str)

expected_as_date: date = expected_as_datetime.date()
expected_as_date_srt: str = "2024-07-31"

expected_as_datetime_tz_format = DATETIME_FORMAT_OFFSET
expected_as_datetime_format = DATETIME_FORMAT_DEFAULT
expected_as_date_format = DATE_FORMAT_ISO


@pytest.mark.parametrize("expected, other, dt_min, dt_max, dt_str_format, tz, should_equal", [
    # datetime (without timezone) vs datetime (without timezone)
    (expected_as_datetime, expected_as_datetime, None, None, expected_as_datetime_format, None, True),
    (expected_as_datetime, date_time_plus_timedelta(expected_as_datetime, seconds=-1), None, None, expected_as_datetime_format, None, False),
    (expected_as_datetime, date_time_plus_timedelta(expected_as_datetime, seconds=-1), timedelta(minutes=1), None, expected_as_datetime_format, None, True),
    (expected_as_datetime, date_time_plus_timedelta(expected_as_datetime, minutes=2), None, timedelta(minutes=2), expected_as_datetime_format, None, True),
    (expected_as_datetime, date_time_plus_timedelta(expected_as_datetime, minutes=-2), timedelta(minutes=1), timedelta(minutes=2), expected_as_datetime_format, None, False),
    (expected_as_datetime, date_time_plus_timedelta(expected_as_datetime, minutes=3), timedelta(minutes=1), timedelta(minutes=2), expected_as_datetime_format, None, False),

    # datetime (with timezone) vs datetime (with timezone)
    (expected_as_datetime_tz, expected_as_datetime_tz, None, None, expected_as_datetime_tz_format, None, True),
    (expected_as_datetime_tz, date_time_plus_timedelta(expected_as_datetime_tz, seconds=-1), None, None, expected_as_datetime_tz_format, None, False),
    (expected_as_datetime_tz, date_time_plus_timedelta(expected_as_datetime_tz, seconds=-1), timedelta(minutes=1), None, expected_as_datetime_tz_format, None, True),
    (expected_as_datetime_tz, date_time_plus_timedelta(expected_as_datetime_tz, seconds=2), None, timedelta(minutes=2), expected_as_datetime_tz_format, None, True),
])
def test_compare_datetime_datetime(expected, other, dt_min, dt_max, dt_str_format, tz, should_equal):
    dtc = DatetimeCompare(expected, dt_min, dt_max, dt_str_format=dt_str_format, tz=tz)
    assert (dtc == other) == should_equal


@pytest.mark.parametrize("expected, other, dt_str_format, expected_error, as_datetime", [
    (expected_as_datetime_tz, expected_as_datetime, expected_as_datetime_format, TypeError, True),
    (expected_as_datetime, expected_as_datetime_tz, expected_as_datetime_tz_format, TypeError, True),
    (expected_as_datetime, expected_as_date, expected_as_date_format, TypeError, True),
    (expected_as_date, expected_as_datetime, expected_as_date_format, TypeError, False),
    (expected_as_datetime, "2024-10-09T10:00:00Z", expected_as_datetime_format, ValueError, True),
    (expected_as_date, "2015-31-31", expected_as_date_format, ValueError, False),
])
def test_compare_errors(expected, other, dt_str_format, expected_error, as_datetime):
    _func = DatetimeCompare if as_datetime else DateCompare
    dtc = _func(expected, dt_str_format=dt_str_format)
    with pytest.raises(expected_error):
        dtc == other


@pytest.mark.parametrize("expected, other, dt_str_format, tz, should_equal", [
    # datetime (without timezone) vs datetime (without timezone)
    (expected_as_datetime, expected_as_str, expected_as_datetime_format, None, True),
    (expected_as_datetime, "2024-07-31 14:00:30", expected_as_datetime_format, None, False),

    # datetime (with timezone) vs datetime (with timezone)
    (expected_as_datetime_tz, expected_as_str_tz, expected_as_datetime_tz_format, timezone.utc, True),
    (expected_as_datetime_tz, expected_as_str_tz, expected_as_datetime_tz_format, None, True),
    (expected_as_datetime_tz, "2024-08-09T10:00:30+01:00", expected_as_datetime_tz_format, None, False),
    (expected_as_datetime_tz, "2024-08-09T10:00:30+01:00", expected_as_datetime_tz_format, timezone.utc, False),
    (expected_as_datetime_tz, "2024-08-09T12:00:30+02:00", expected_as_datetime_tz_format, None, True),
    (expected_as_datetime_tz, "2024-08-09T08:00:30-02:00", expected_as_datetime_tz_format, None, True),
    (expected_as_datetime_tz, "2024-08-09 10:00:30", expected_as_datetime_format, timezone.utc, True),
    (expected_as_datetime_tz, "2024-08-09 09:00:30", expected_as_datetime_format, timezone.utc, False),
    (expected_as_datetime_tz, "2024-08-09 11:00:30", expected_as_datetime_format, timezone.utc, False),
])
def test_compare_datetime_str(expected, other, dt_str_format, tz, should_equal):
    dtc = DatetimeCompare(expected, dt_str_format=dt_str_format, tz=tz)
    assert (dtc == other) == should_equal


def test_compare_str_datetime():
    dtc = DatetimeCompare(expected_as_str, timedelta(minutes=1), timedelta(minutes=2), dt_str_format=expected_as_datetime_format)

    valid = (
        expected_as_datetime - timedelta(seconds=59),
        expected_as_datetime,
        expected_as_datetime + timedelta(seconds=119),
    )
    invalid = (
        expected_as_datetime - timedelta(seconds=61),
        expected_as_datetime + timedelta(seconds=121),
        expected_as_datetime - timedelta(days=1),
        expected_as_datetime + timedelta(days=1),
    )
    for value in valid:
        assert dtc == value, f"{dtc} is not equal to {value}"
    for value in invalid:
        assert dtc != value, f"{dtc} is not different than {value}"


def test_compare_date_date():
    dtc = DateCompare(expected_as_date, timedelta(days=1), timedelta(days=2), dt_str_format=expected_as_date_format)

    valid = (
        expected_as_date - timedelta(days=1),
        expected_as_date,
        expected_as_date + timedelta(days=2),
    )
    invalid = (
        expected_as_date - timedelta(days=2),
        expected_as_date + timedelta(days=3),
    )
    for value in valid:
        assert dtc == value, f"{dtc} is not equal to {value}"
    for value in invalid:
        assert dtc != value, f"{dtc} is not different than {value}"


def test_compare_date_str():
    dtc = DateCompare(expected_as_date, timedelta(days=1), timedelta(days=2), dt_str_format=expected_as_date_format)

    valid = (
        (expected_as_date - timedelta(days=1)).isoformat(),
        (expected_as_date + timedelta(days=2)).isoformat(),
        expected_as_date_srt,
        "2024-07-30",
        "2024-08-01",
        "2024-08-02",
    )
    invalid = (
        (expected_as_date - timedelta(days=2)).isoformat(),
        (expected_as_date + timedelta(days=3)).isoformat(),
        "2024-07-29",
        "2024-08-03",
    )
    for value in valid:
        assert dtc == value, f"{dtc} is not equal to {value}"
    for value in invalid:
        assert dtc != value, f"{dtc} is not different than {value}"


def test_compare_str_date():
    dtc = DateCompare(expected_as_str, timedelta(days=1), timedelta(days=2), dt_str_format=expected_as_datetime_format)

    valid = (
        expected_as_date - timedelta(days=1),
        expected_as_date,
        expected_as_date + timedelta(days=2),
    )
    invalid = (
        expected_as_date - timedelta(days=2),
        expected_as_date + timedelta(days=3),
    )
    for value in valid:
        assert dtc == value, f"{dtc} is not equal to {value}"
    for value in invalid:
        assert dtc != value, f"{dtc} is not different than {value}"


@pytest.mark.parametrize("expected, other, dt_str_format, tz, should_equal", [
    # datetime (without timezone) vs datetime (without timezone)
    ("2024-10-09 09:59:35", "2024-10-09 09:58:35", DATETIME_FORMAT_DEFAULT, None, True),
    ("2024-10-09 09:59:35", "2024-10-09 10:01:35", DATETIME_FORMAT_DEFAULT, None, True),
    ("2024-10-09T09:59:35", "2024-10-09T10:01:35", DATETIME_FORMAT_ISO, None, True),

    # datetime (with timezone) vs datetime (with timezone)
    ("2024-10-09 09:59:35", "2024-10-09 09:58:35", DATETIME_FORMAT_DEFAULT, "Portugal", True),
    ("2024-10-09T09:59:35+02:00", "2024-10-09T09:58:35+02:00", DATETIME_FORMAT_OFFSET, None, True),
    ("2024-10-09T09:59:35+02:00", "2024-10-09T07:58:35+00:00", DATETIME_FORMAT_OFFSET, None, True),
    ("2024-10-09T09:59:35+02:00", "2024-10-09T06:58:35+00:00", DATETIME_FORMAT_OFFSET, None, False),
])
def test_compare_str_str_for_datetime(expected, other, dt_str_format, tz, should_equal):
    dtc = DatetimeCompare(expected, timedelta(minutes=1), timedelta(minutes=2), dt_str_format=dt_str_format, tz=tz)
    assert (dtc == other) == should_equal


def test_compare_str_str_for_date():
    dtc = DateCompare("2024-10-09", timedelta(days=1), timedelta(days=2), dt_str_format=expected_as_date_format)

    valid = (
        "2024-10-08",
        "2024-10-11",
    )
    invalid = (
        "2024-10-07",
        "2024-10-12",
    )
    for value in valid:
        assert dtc == value, f"{dtc} is not equal to {value}"
    for value in invalid:
        assert dtc != value, f"{dtc} is not different than {value}"


def test_now_today():
    _now = now()
    _today = today()

    assert _today == _now.date()
    assert yesterday() == _now.date() - timedelta(days=1)
    assert tomorrow() == _now.date() + timedelta(days=1)
    assert yesterday() == _today - timedelta(days=1)
    assert tomorrow() == _today + timedelta(days=1)

    midnight_ = datetime(2024, 10, 29, 0, 0, 0, tzinfo=timezone.utc)

    assert midnight(midnight_.date()) == midnight_


def test_date_methods():
    _date = date(2024, 12, 31)
    _date_str = "2024-12-31"

    assert date_to_string(_date) == _date_str
    assert string_to_date(_date_str) == _date
    assert string_to_date(date_to_string(_date)) == _date
    assert date_to_string(string_to_date(_date_str)) == _date_str

    assert date_to_string(date_time_plus_timedelta(_date, days=-2)) == "2024-12-29"
    assert date_to_string(date_time_plus_timedelta(_date, days=1)) == "2025-01-01"

    assert date_to_string(_date, format_="%m %d/%Y") == "12 31/2024"


def test_datetime_methods():
    _date = datetime(2024, 8, 31, 23, 35, 30, tzinfo=timezone.utc)
    _date2 = change_timezone(datetime(2024, 8, 31, 23, 35, 30, tzinfo=timezone.utc), "Portugal")
    _date_str = "2024-08-31 23:35:30"
    _date_tz2 = "2024-09-01 00:35:30"

    assert _date_str == datetime_to_string(replace_timezone(_date, "Portugal"))
    assert _date_tz2 == datetime_to_string(change_timezone(_date, "Portugal"))

    assert _date_str == datetime_to_string(_date)
    assert _date == replace_timezone(string_to_datetime(_date_str))
    assert _date == string_to_datetime(datetime_to_string(_date))
    assert _date_str == datetime_to_string(string_to_datetime(_date_str))

    assert "2024-08-29 23:35:30" == datetime_to_string(date_time_plus_timedelta(_date, days=-2))
    assert "2024-09-01 23:35:30" == datetime_to_string(date_time_plus_timedelta(_date, days=1))
    assert "08 31/2024 30-35:23" == datetime_to_string(_date, format_="%m %d/%Y %S-%M:%H")

    assert "2024-08-31T23:35:30" == isoformat_no_tz(_date)
    assert "2024-08-31 23:35:30" == isoformat_no_tz(_date, sep=" ")
    assert "2024-08-31T23:35:30Z" == isoformat_with_tz(_date)
    assert "2024-08-31 23:35:30Z" == isoformat_with_tz(_date, sep=" ")
    assert "2024-08-31T23:35:30+00:00" == isoformat_with_offset(_date)
    assert "2024-08-31 23:35:30+00:00" == isoformat_with_offset(_date, sep=" ")
    assert "2024-09-01 00:35:30+01:00" == isoformat_with_offset(_date2, sep=" ")
