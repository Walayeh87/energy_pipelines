import logging

from pandas import Series

from data_source.energy_charts.energy_price.price_col_name_in_db import (
    PriceDataColNameInDB,
)

logger = logging.getLogger(__name__)


def process_fetched_energy_prices_from_db(raw_data: list[dict]) -> Series:
    series = Series(
        data=[item.get(PriceDataColNameInDB.ENERGY_PRICE) for item in raw_data],
        index=[item.get(PriceDataColNameInDB.TIMESTAMP) for item in raw_data],
    )

    logger.info("Energy prices have been processed successfully.")

    return series
