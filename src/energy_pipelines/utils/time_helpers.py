from datetime import datetime, timedelta


def get_tomorrows_date() -> datetime:
    date = datetime.now().date() + timedelta(days=1)
    return datetime(year=date.year, month=date.month, day=date.day)
