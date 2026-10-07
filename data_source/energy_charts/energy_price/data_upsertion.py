import logging
from typing import LiteralString

from pandas import DataFrame
from psycopg import Connection

from data_source.energy_charts.energy_price.price_col_name_in_db import (
    PriceDataColNameInDB,
)

logger = logging.getLogger(__name__)


def upsert_df_to_db(df: DataFrame, db_connection: Connection, upsert_sql_query: LiteralString) -> None:
    rows = [
        (
            row[PriceDataColNameInDB.TIMESTAMP],
            row[PriceDataColNameInDB.PRICE_METADATA_ID],
            row[PriceDataColNameInDB.ENERGY_PRICE],
        )
        for _, row in df.iterrows()
    ]

    with db_connection.cursor() as cursor:
        cursor.executemany(upsert_sql_query, rows)

    logger.info(f"{len(rows)} energy prices have been loaded to the database.")

    db_connection.commit()
    db_connection.close()
