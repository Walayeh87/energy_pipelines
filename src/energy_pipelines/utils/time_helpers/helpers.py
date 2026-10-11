import pytz
from pandas import Timestamp


def get_current_date() -> Timestamp:
    return Timestamp.now(tz=pytz.UTC)
