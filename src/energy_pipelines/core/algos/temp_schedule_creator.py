from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame, Timedelta


def create_temp_schedule(
    prices: DataFrame,
    min_temp: float,
    max_temp: float,
    default_temp: float,
) -> DataFrame:
    # No need to check empty prices since this case is handled in temp_schedule_pipeline.py
    if min_temp > max_temp:
        raise ValueError("min_temp must be <= max_temp.")

    if not np.isfinite(prices.to_numpy(dtype=float)).all():
        raise ValueError("Energy prices must be finite numeric values.")

    min_price = prices.min().min()
    max_price = prices.max().max()

    if min_price == max_price:
        return DataFrame([default_temp], index=prices.index)

    normalized_prices = (prices - min_price) / (max_price - min_price)

    temp_schedule = min_temp + normalized_prices * (max_temp - min_temp)

    return temp_schedule


def create_backup_temp_schedule(
    start: datetime,
    end: datetime,
    algo_freq: str,
    default_temp: float,
    tz: str,
) -> DataFrame:
    index = pd.date_range(start=start, end=end - Timedelta(algo_freq), freq=algo_freq, tz=tz)
    return DataFrame([default_temp] * len(index), index=index)
