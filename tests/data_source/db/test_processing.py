from data_source.db.energy_price.processing import process_fetched_energy_prices_from_db
from data_source.energy_charts.energy_price.price_col_name_in_db import (
    PriceDataColNameInDB,
)
from pandas import Series


def test_process_fetched_energy_prices_from_db() -> None:
    real_dict_rows = [
        {
            PriceDataColNameInDB.TIMESTAMP: "2026-06-01T00:00:00",
            PriceDataColNameInDB.ENERGY_PRICE: 50.0,
        },
        {
            PriceDataColNameInDB.TIMESTAMP: "2026-06-01T01:00:00",
            PriceDataColNameInDB.ENERGY_PRICE: 55.0,
        },
    ]

    series = process_fetched_energy_prices_from_db(raw_data=real_dict_rows)

    assert isinstance(series, Series)
    assert series.index.tolist() == ["2026-06-01T00:00:00", "2026-06-01T01:00:00"]
    assert series.tolist() == [50.0, 55.0]
