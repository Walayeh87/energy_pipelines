from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from energy_pipelines.utils.time_constant import TimeConstant


def get_tomorrows_date(tz: str) -> datetime:
    try:
        ZoneInfo(tz)
    except ZoneInfoNotFoundError as e:
        raise ZoneInfoNotFoundError(f"Invalid timezone: {tz}") from e

    date = datetime.now(tz=ZoneInfo(tz)).date() + timedelta(days=1)
    return datetime(year=date.year, month=date.month, day=date.day, tzinfo=ZoneInfo(tz))


def get_tz_diff_in_h(
    target_tz: str,
    reference_tz: str = "UTC",
    dt: datetime | None = None,
) -> float:
    """Return the time difference in hours: reference_tz - target_tz."""
    try:
        ZoneInfo(target_tz)
    except ZoneInfoNotFoundError as e:
        raise ZoneInfoNotFoundError(f"Invalid timezone: {target_tz}") from e

    try:
        ZoneInfo(reference_tz)
    except ZoneInfoNotFoundError as e:
        raise ZoneInfoNotFoundError(f"Invalid timezone: {reference_tz}") from e

    dt = dt or datetime.now(ZoneInfo(target_tz))

    target_time = dt.astimezone(ZoneInfo(target_tz))
    reference_time = dt.astimezone(ZoneInfo(reference_tz))

    return (reference_time.utcoffset() - target_time.utcoffset()).total_seconds() / TimeConstant.SEC_IN_H


if __name__ == "__main__":
    tz_diff = get_tz_diff_in_h("Europe/Berlin")
    tomorrow = get_tomorrows_date("Europe/Berlin")
    print(f"Time difference: {tz_diff} hours")
    print(f"Tomorrow's date: {tomorrow}")
