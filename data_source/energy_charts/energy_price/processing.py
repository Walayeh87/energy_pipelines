import logging
from typing import Any

import pandas as pd
from pandas import DataFrame

from data_source.energy_charts.energy_price.price_col_name_in_db import (
    PriceDataColNameInDB,
)
from data_source.energy_charts.energy_price.price_key_in_energy_charts import (
    PriceKeyInEnergyCharts,
)

logger = logging.getLogger(__name__)


def process_fetched_energy_price_from_external_source(
    data_as_dict: dict[str, Any],
    price_metadata_id: int,
) -> DataFrame:
    if len(data_as_dict) == 0:
        raise ValueError("data_as_dict must not be empty.")

    if (len(data_as_dict[PriceKeyInEnergyCharts.UNIX_SECONDS]) == 0) or (
        len(data_as_dict[PriceKeyInEnergyCharts.PRICE]) == 0
    ):
        raise ValueError(
            f"{PriceKeyInEnergyCharts.UNIX_SECONDS} and/or {PriceKeyInEnergyCharts.PRICE} contain(s) no data."
        )

    timestamp = DataFrame(data_as_dict[PriceKeyInEnergyCharts.UNIX_SECONDS])
    timestamp = timestamp.rename(columns={timestamp.columns[0]: PriceDataColNameInDB.TIMESTAMP})

    energy_price = DataFrame(data_as_dict[PriceKeyInEnergyCharts.PRICE])
    energy_price = energy_price.rename(columns={energy_price.columns[0]: PriceDataColNameInDB.ENERGY_PRICE})

    data_as_df = pd.concat([timestamp, energy_price], axis="columns")
    data_as_df[PriceDataColNameInDB.PRICE_METADATA_ID] = price_metadata_id.value
    data_as_df[PriceDataColNameInDB.TIMESTAMP] = pd.to_datetime(
        data_as_df[PriceDataColNameInDB.TIMESTAMP], unit="s", utc=True
    )
    data_as_df = data_as_df[
        [
            PriceDataColNameInDB.TIMESTAMP,
            PriceDataColNameInDB.PRICE_METADATA_ID,
            PriceDataColNameInDB.ENERGY_PRICE,
        ]
    ]

    logger.info("Energy prices have been processed successfully.")

    return data_as_df


if __name__ == "__main__":
    data_as_dict = {
        "unix_seconds": [1700000000, 1700003600],
        "price": [50.0, 51.0],
        "unit": "EUR/MWh",
    }
    price_as_df = process_fetched_energy_price_from_external_source(
        data_as_dict=data_as_dict, price_metadata_id=int(value=1)
    )
    print(price_as_df)
