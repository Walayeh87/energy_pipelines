import pandas as pd
import pytest
from data_source.energy_charts.energy_price.price_col_name_in_db import (
    PriceDataColNameInDB,
)
from pandas import DataFrame, Series, Timestamp

from data_source.energy_charts.energy_price.price_key_in_energy_charts import (
    PriceKeyInEnergyCharts,
)
from data_source.energy_charts.energy_price.processing import (
    process_fetched_energy_price_from_external_source,
)


def test_convert_energy_price_from_dict_to_df_with_empty_dict() -> None:
    with pytest.raises(ValueError):
        process_fetched_energy_price_from_external_source(data_as_dict={}, price_metadata_id=int(value=1))


def test_convert_energy_price_from_dict_to_df_with_empty_keys() -> None:
    with pytest.raises(ValueError):
        data_as_dict = {
            PriceKeyInEnergyCharts.UNIX_SECONDS: [],
            PriceKeyInEnergyCharts.PRICE: [],
        }
        process_fetched_energy_price_from_external_source(data_as_dict=data_as_dict, price_metadata_id=int(value=1))


def test_convert_energy_price_from_dict_to_df() -> None:
    data_as_dict = {
        PriceKeyInEnergyCharts.UNIX_SECONDS: [1700000000, 1700003600],
        PriceKeyInEnergyCharts.PRICE: [50.0, 51.0],
    }
    data_as_df = process_fetched_energy_price_from_external_source(
        data_as_dict=data_as_dict, price_metadata_id=1
    )

    assert isinstance(data_as_df, DataFrame)
    assert len(data_as_df) == 2
    assert list(data_as_df) == [
        PriceDataColNameInDB.TIMESTAMP,
        PriceDataColNameInDB.PRICE_METADATA_ID,
        PriceDataColNameInDB.ENERGY_PRICE,
    ]

    pd.testing.assert_series_equal(
        data_as_df[PriceDataColNameInDB.TIMESTAMP],
        Series(
            [
                Timestamp("2023-11-14 22:13:20+00:00", unit="us"),
                Timestamp("2023-11-14 23:13:20+00:00", unit="us"),
            ]
        ),
        check_dtype=False,
        check_names=False,
    )

    pd.testing.assert_series_equal(
        data_as_df[PriceDataColNameInDB.PRICE_METADATA_ID],
        Series([1, 1]),
        check_names=False,
    )

    pd.testing.assert_series_equal(
        data_as_df[PriceDataColNameInDB.ENERGY_PRICE],
        Series([50.0, 51.0]),
        check_names=False,
    )
