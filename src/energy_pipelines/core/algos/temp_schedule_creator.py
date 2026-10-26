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
    """Create a temperature schedule based on energy price levels.

    The function normalizes the input price values to the range [0, 1] using the
    minimum and maximum observed prices, then maps that normalized range to the
    temperature interval [min_temp, max_temp]. When all prices are equal, it returns
    a fallback row of the default temperature aligned to the input index.

    The function is naive. It does not take into account creating ramps between schedules consecutive days.

    Args:
        prices: DataFrame of energy prices whose values are used to derive the schedule.
        min_temp: Lower bound of the temperature range.
        max_temp: Upper bound of the temperature range.
        default_temp: Temperature value to use when the price range collapses to a single value.

    Returns:
        A DataFrame representing the generated temperature schedule.

    Raises:
        ValueError: If `min_temp` exceeds `max_temp`, or if any price value is not finite.
    """
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
    """Create a constant fallback temperature schedule over the unreceived energy price date range.

    This helper generates a pandas time index from `start` to `end` using the supplied
    frequency, and fills every interval with the same default temperature.

    Args:
        start: Start timestamp for the schedule range.
        end: End timestamp for the schedule range.
        algo_freq: Frequency string for the datetime index, e.g. "15min" or "1h".
        default_temp: Constant temperature assigned to each generated timestamp.
        tz: Timezone used for the resulting timestamps.

    Returns:
        A DataFrame containing a constant temperature for each timestamp in the range.
    """
    index = pd.date_range(start=start, end=end - Timedelta(algo_freq), freq=algo_freq, tz=tz)
    return DataFrame([default_temp] * len(index), index=index)
