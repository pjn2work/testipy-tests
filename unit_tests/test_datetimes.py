import pytz

from common.utils.datetimes import *


expected_as_str = "2024-10-09T10:00:30"
expected_as_datetime: datetime = datetime.fromisoformat(expected_as_str)
expected_as_date: date = expected_as_datetime.date()
expected_as_datetime_format = DATETIME_FORMAT_ISO
expected_as_date_format = DATE_FORMAT_ISO


def test_compare_datetime_datetime():
    dtc = DatetimeCompare(expected_as_datetime, timedelta(minutes=1), timedelta(minutes=2), dt_format=expected_as_datetime_format)

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


def test_compare_datetime_date():
    dtc = DatetimeCompare(expected_as_datetime, timedelta(days=1), timedelta(days=2), dt_format=expected_as_datetime_format)

    invalid = (
        expected_as_date - timedelta(days=1),
        expected_as_date,
        expected_as_date + timedelta(days=2),

        expected_as_date - timedelta(days=2),
        expected_as_date + timedelta(days=3),
    )
    for value in invalid:
        try:
            assert dtc != value, f"{dtc} is not different than {value}"
        except TypeError:
            pass


def test_compare_date_datetime():
    dtc = DatetimeCompare(expected_as_date, timedelta(days=1), timedelta(days=2), dt_format=expected_as_date_format)

    invalid = (
        expected_as_datetime - timedelta(days=1),
        expected_as_datetime,
        expected_as_datetime + timedelta(days=2),

        expected_as_datetime - timedelta(days=2),
        expected_as_datetime + timedelta(days=3),
    )
    for value in invalid:
        try:
            assert dtc != value, f"{dtc} is not different than {value}"
        except TypeError:
            pass


def test_compare_datetime_str():
    dtc = DatetimeCompare(expected_as_datetime, timedelta(minutes=1), timedelta(minutes=2), dt_format=expected_as_datetime_format)

    valid = (
        (expected_as_datetime - timedelta(seconds=59)).isoformat(),
        expected_as_str,
        (expected_as_datetime + timedelta(seconds=119)).isoformat(),
        "2024-10-09T09:59:35",
        "2024-10-09T10:02:29",
    )
    invalid = (
        (expected_as_datetime - timedelta(seconds=61)).isoformat(),
        (expected_as_datetime + timedelta(seconds=121)).isoformat(),
        (expected_as_datetime - timedelta(days=1)).isoformat(),
        (expected_as_datetime + timedelta(days=1)).isoformat(),
        "2024-10-09T09:59:29",
        "2024-10-09T10:02:31",
    )
    for value in valid:
        assert dtc == value, f"{dtc} is not equal to {value}"
    for value in invalid:
        assert dtc != value, f"{dtc} is not different than {value}"


def test_compare_str_datetime():
    dtc = DatetimeCompare(expected_as_str, timedelta(minutes=1), timedelta(minutes=2), dt_format=expected_as_datetime_format, expected_type="datetime")

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
    dtc = DatetimeCompare(expected_as_date, timedelta(days=1), timedelta(days=2), dt_format=expected_as_date_format)

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
    dtc = DatetimeCompare(expected_as_date, timedelta(days=1), timedelta(days=2), dt_format=expected_as_date_format)

    valid = (
        (expected_as_date - timedelta(days=1)).isoformat(),
        (expected_as_date + timedelta(days=2)).isoformat(),
        "2024-10-08",
        "2024-10-09",
        "2024-10-11",
    )
    invalid = (
        (expected_as_date - timedelta(days=2)).isoformat(),
        (expected_as_date + timedelta(days=3)).isoformat(),
        "2024-10-07",
        "2024-10-12",
    )
    for value in valid:
        assert dtc == value, f"{dtc} is not equal to {value}"
    for value in invalid:
        assert dtc != value, f"{dtc} is not different than {value}"


def test_compare_str_date():
    dtc = DatetimeCompare(expected_as_str, timedelta(days=1), timedelta(days=2), dt_format=expected_as_datetime_format, expected_type="date")

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


def test_compare_str_str_for_datetime():
    dtc = DatetimeCompare(expected_as_str, timedelta(minutes=1), timedelta(minutes=2), dt_format=expected_as_datetime_format, expected_type="datetime")

    valid = (
        expected_as_str,
        "2024-10-09T09:59:35",
        "2024-10-09T10:02:29",
    )
    invalid = (
        "2024-10-09T09:59:29",
        "2024-10-09T10:02:31",
    )
    for value in valid:
        assert dtc == value, f"{dtc} is not equal to {value}"
    for value in invalid:
        assert dtc != value, f"{dtc} is not different than {value}"


def test_compare_str_str_for_date():
    dtc = DatetimeCompare("2024-10-09", timedelta(days=1), timedelta(days=2), dt_format=expected_as_date_format, expected_type="date")

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

    assert datetime_to_string(replace_timezone(_date, "Portugal")) == _date_str
    assert datetime_to_string(change_timezone(_date, "Portugal")) == _date_tz2

    assert datetime_to_string(_date) == _date_str
    assert replace_timezone(string_to_datetime(_date_str)) == _date
    assert string_to_datetime(datetime_to_string(_date)) == _date
    assert datetime_to_string(string_to_datetime(_date_str)) == _date_str

    assert datetime_to_string(date_time_plus_timedelta(_date, days=-2)) == "2024-08-29 23:35:30"
    assert datetime_to_string(date_time_plus_timedelta(_date, days=1)) == "2024-09-01 23:35:30"
    assert datetime_to_string(_date, format_="%m %d/%Y %S-%M:%H") == "08 31/2024 30-35:23"


    assert isoformat_no_tz(_date) == "2024-08-31T23:35:30"
    assert isoformat_no_tz(_date, sep=" ") == "2024-08-31 23:35:30"
    assert isoformat_with_tz(_date) == "2024-08-31T23:35:30Z"
    assert isoformat_with_tz(_date, sep=" ") == "2024-08-31 23:35:30Z"
    assert isoformat_with_offset(_date) == "2024-08-31T23:35:30+00:00"
    assert isoformat_with_offset(_date, sep=" ") == "2024-08-31 23:35:30+00:00"
    assert isoformat_with_offset(_date2, sep=" ") == "2024-09-01 00:35:30+01:00"
