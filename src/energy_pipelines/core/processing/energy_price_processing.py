import logging
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

import pandas as pd
from pandas import Timedelta
from pandas.core.frame import DataFrame
from pandas.core.series import Series
from sqlalchemy.orm import Session
from tspropy import (
    convert_timedelta_to_human_format,
    infer_index_freq,
    split_df_into_list_of_phases,
)

from energy_pipelines.core.database.connection import create_db_engine, create_db_session
from energy_pipelines.core.database.data_fetchers_from_db import (
    DTFetchingResult,
    fetch_dt_data,
    fetch_price_metadata,
)
from energy_pipelines.core.database.models import PriceData, PriceMetadata, SchemaNames

logger = logging.getLogger(__name__)


class ProcessingIssues(StrEnum):
    NONE = "None"

    FREQUENCY_MISMATCH = "Frequency Mismatch"
    MISSING_VALUES = "Missing Values"
    EMPTY_DATA = "Empty"
    UNKNOWN = "Unknown"


@dataclass
class EnergyPriceProcessingResult:
    original_prices: DataFrame
    processed_prices: DataFrame

    mask_of_filled_values: Series
    processing_issue: ProcessingIssues


def process_energy_price_data(
    session: Session,
    fetching_result: DTFetchingResult,
) -> EnergyPriceProcessingResult:
    prices_as_list = fetching_result.dt_data
    if len(prices_as_list) == 0:
        logger.warning(
            f"No price data found for the specified period:"
            f" {fetching_result.start} to {fetching_result.end}"
            f" for {PriceMetadata.price_metadata_id.key} {fetching_result.data_id} in "
            f"{SchemaNames.ENERGY_PRICES}.{PriceMetadata.__tablename__}"
        )
        return EnergyPriceProcessingResult(
            original_prices=DataFrame(),
            processed_prices=DataFrame(),
            mask_of_filled_values=Series(dtype=bool),
            processing_issue=ProcessingIssues.EMPTY_DATA,
        )

    price_metadata = fetch_price_metadata(session=session, metadata_id=fetching_result.data_id)

    prices = DataFrame(prices_as_list)
    prices = prices.set_index(PriceData.timestamp.key)
    prices.index = prices.index.tz_convert(price_metadata.tz)

    original_prices = prices

    db_freq_as_str = str(price_metadata.freq)
    db_freq = Timedelta(db_freq_as_str)
    actual_freq = infer_index_freq(index=prices.index)
    actual_freq_as_str = convert_timedelta_to_human_format(timedelta=actual_freq)

    expected_index = pd.date_range(
        start=fetching_result.start,
        end=fetching_result.end - db_freq,
        freq=db_freq,
        tz=str(price_metadata.tz),
    )

    no_missing_prices = not prices[PriceData.energy_price.key].isna().any()
    indices_match = prices.index.equals(expected_index)
    if indices_match and no_missing_prices:
        logger.info("Energy price data is already in the expected format.")
        return EnergyPriceProcessingResult(
            original_prices=original_prices,
            processed_prices=original_prices,
            mask_of_filled_values=Series([False] * len(prices), index=prices.index),
            processing_issue=ProcessingIssues.NONE,
        )

    if db_freq != actual_freq:
        logger.error(
            f"Energy price frequency mismatch: expected '{db_freq_as_str}', got '{actual_freq_as_str}'"
        )
        return EnergyPriceProcessingResult(
            original_prices=original_prices,
            processed_prices=original_prices,
            mask_of_filled_values=Series([False] * len(prices), index=prices.index),
            processing_issue=ProcessingIssues.FREQUENCY_MISMATCH,
        )

    duration = fetching_result.end - fetching_result.start
    expected_prices_count = duration // db_freq
    actual_prices_count = len(prices)

    has_length_mismatch = expected_prices_count != actual_prices_count
    contains_nans = prices[PriceData.energy_price.key].isna().any()
    if has_length_mismatch or contains_nans:
        logger.warning("Energy prices contain missing values and/or indices.")

        prices = prices.reindex(expected_index)
        mask_of_nans = prices[PriceData.energy_price.key].isna()
        missing_values_before = prices[PriceData.energy_price.key].isna().sum()

        prices = _fill_inner_missing_energy_prices(prices=prices)
        if prices[PriceData.energy_price.key].isna().any():
            logger.warning(
                "Some/all missing prices are on the beginning or the end of the fetched prices. "
                "Nearest prices will be used to close the gaps."
            )
            prices = _fill_outer_missing_energy_prices(prices=prices)

        missing_values_after = prices[PriceData.energy_price.key].isna().sum()
        filled_values_count = missing_values_before - missing_values_after

        logger.info(f"{filled_values_count} price value(s) was/were filled.")

        return EnergyPriceProcessingResult(
            original_prices=original_prices,
            processed_prices=prices,
            mask_of_filled_values=mask_of_nans,
            processing_issue=ProcessingIssues.MISSING_VALUES,
        )
    else:
        logger.warning("Energy prices have an unknown issue. The original data is passed without processing.")

        return EnergyPriceProcessingResult(
            original_prices=original_prices,
            processed_prices=original_prices,
            mask_of_filled_values=Series([False] * len(original_prices), index=original_prices.index),
            processing_issue=ProcessingIssues.UNKNOWN,
        )


def _fill_inner_missing_energy_prices(prices: DataFrame) -> DataFrame:
    prices = prices.copy()

    hour_ids = "hour_id"
    prices[hour_ids] = prices.index.floor("h").factorize()[0]

    list_of_phases = split_df_into_list_of_phases(df=prices, phase_nr_col=hour_ids)

    filled_phases = []
    for phase in list_of_phases:
        filled_phase = phase.astype(float).ffill()
        filled_phase = filled_phase.astype(float).bfill()
        filled_phases.append(filled_phase)

    filled_prices = pd.concat(filled_phases)
    filled_prices = filled_prices.drop(columns=[hour_ids])

    return filled_prices


def _fill_outer_missing_energy_prices(prices: DataFrame) -> DataFrame:
    filled_prices = prices.astype(float).ffill()
    filled_prices = filled_prices.astype(float).bfill()

    return filled_prices


if __name__ == "__main__":
    db_engine = create_db_engine()
    session = create_db_session(db_engine)

    start_date = datetime(2026, 7, 1)
    end_date = datetime(2026, 7, 2)
    fetching_result = fetch_dt_data(
        session=session,
        cols2fetch=[PriceData.timestamp, PriceData.energy_price],
        data_id=1,
        start=start_date,
        end=end_date,
    )

    result = process_energy_price_data(session, fetching_result)
