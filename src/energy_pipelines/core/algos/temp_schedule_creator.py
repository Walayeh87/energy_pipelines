import pandas as pd
from pandas import Timedelta
from pandas.core.frame import DataFrame

from energy_pipelines.utils.time_helpers import get_tomorrows_date


def create_backup_temp_schedule(
    algo_freq: str,
    default_temp: float | int,
    tz: str,
) -> DataFrame:
    index = pd.date_range(
        start=get_tomorrows_date(),
        end=get_tomorrows_date() + Timedelta(days=1) - Timedelta(algo_freq),
        freq=algo_freq,
        tz=tz,
    )
    return DataFrame([default_temp] * len(index), index=index)
