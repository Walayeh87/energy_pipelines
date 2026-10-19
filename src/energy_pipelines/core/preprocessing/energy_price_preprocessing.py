import logging
from typing import Any

import pandas as pd
from pandas import DataFrame

from energy_pipelines.core.database.api_models import EnergyChartsKeys
from energy_pipelines.core.database.table_models import PriceData

logger = logging.getLogger(__name__)


def preprocess_price_data(
    prices_as_dict: dict[str, Any],
    price_metadata_id: int,
) -> DataFrame:
    timestamp_key = PriceData.timestamp.key

    df = _convert_energy_price_to_df(data_as_dict=prices_as_dict, price_metadata_id=price_metadata_id)
    df = df.drop_duplicates(timestamp_key)
    df = df.sort_values(timestamp_key)

    logger.info("Energy prices have been processed successfully.")

    return df


def _convert_energy_price_to_df(
    data_as_dict: dict[str, Any],
    price_metadata_id: int,
) -> DataFrame:
    if len(data_as_dict) == 0:
        raise ValueError("data_as_dict must not be empty.")

    if (len(data_as_dict[EnergyChartsKeys.UNIX_SECONDS]) == 0) or (
        len(data_as_dict[EnergyChartsKeys.PRICE]) == 0
    ):
        raise ValueError(
            f"{EnergyChartsKeys.UNIX_SECONDS} and/or {EnergyChartsKeys.PRICE} contain(s) no data."
        )

    timestamp_key = PriceData.timestamp.key
    metadata_id_key = PriceData.price_metadata_id.key
    energy_price_key = PriceData.energy_price.key

    timestamp = DataFrame(data_as_dict[EnergyChartsKeys.UNIX_SECONDS])
    timestamp = timestamp.rename(columns={timestamp.columns[0]: timestamp_key})

    energy_price = DataFrame(data_as_dict[EnergyChartsKeys.PRICE])
    energy_price = energy_price.rename(columns={energy_price.columns[0]: energy_price_key})

    data_as_df = pd.concat([timestamp, energy_price], axis="columns")
    data_as_df[metadata_id_key] = price_metadata_id
    data_as_df[timestamp_key] = pd.to_datetime(data_as_df[timestamp_key], unit="s", utc=True)
    data_as_df = data_as_df[[timestamp_key, metadata_id_key, energy_price_key]]

    return data_as_df


if __name__ == "__main__":
    data_as_dict = {
        "unix_seconds": [1700000000, 1700003600],
        "price": [50.0, 51.0],
        "unit": "EUR/MWh",
    }
    price_as_df = _convert_energy_price_to_df(data_as_dict=data_as_dict, price_metadata_id=1)
    print(price_as_df)
