from unittest.mock import MagicMock

import pandas as pd

from data_source.energy_charts.energy_price.data_upsertion import upsert_df_to_db
from data_source.energy_charts.energy_price.price_col_name_in_db import (
    PriceDataColNameInDB,
)


def test_upsert_df_to_db() -> None:
    # Arrange
    ts1 = "2024-01-01 00:00:00"
    id1 = 1
    energy_price1 = 10.5

    ts2 = "2024-01-01 01:00:00"
    id2 = 2
    energy_price2 = 11.0
    df = pd.DataFrame(
        [
            {
                PriceDataColNameInDB.TIMESTAMP: ts1,
                PriceDataColNameInDB.PRICE_METADATA_ID: id1,
                PriceDataColNameInDB.ENERGY_PRICE: energy_price1,
            },
            {
                PriceDataColNameInDB.TIMESTAMP: ts2,
                PriceDataColNameInDB.PRICE_METADATA_ID: id2,
                PriceDataColNameInDB.ENERGY_PRICE: energy_price2,
            },
        ]
    )

    mock_cursor = MagicMock()
    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    sql = "UPSERT_SQL"

    upsert_df_to_db(df, mock_connection, sql)

    # Assert: correct rows passed to executemany
    expected_rows = [(ts1, id1, energy_price1), (ts2, id2, energy_price2)]

    mock_cursor.executemany.assert_called_once_with(sql, expected_rows)

    # Assert DB lifecycle
    mock_connection.commit.assert_called_once()
    mock_connection.close.assert_called_once()
