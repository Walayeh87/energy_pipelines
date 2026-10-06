from datetime import datetime

from data_source.energy_charts.energy_price.price_col_name_in_db import (
    PriceDataColNameInDB,
)
from data_source.utilities.price_structure_in_db import PriceStructureInDB


def create_energy_price_fetching_query(
    price_metadata_id: int,
    start_date: datetime,
    end_date: datetime,
) -> tuple[str, tuple[int, datetime, datetime]]:
    query = f"""
        SELECT
            {PriceDataColNameInDB.TIMESTAMP},
            {PriceDataColNameInDB.ENERGY_PRICE}
        FROM
            {PriceStructureInDB.SCHEMA_NAME}.{PriceStructureInDB.TABLE_NAME}
        WHERE
            {PriceDataColNameInDB.PRICE_METADATA_ID} = %s
            AND {PriceDataColNameInDB.TIMESTAMP} >= %s
            AND {PriceDataColNameInDB.TIMESTAMP} < %s
        ORDER BY
            {PriceDataColNameInDB.TIMESTAMP};
    """

    params = (price_metadata_id, start_date, end_date)

    return query, params


def create_query_for_earliest_timestamp(
    db_start_date: str, shema_name: str, table_name: str, price_metadata_id: int
) -> tuple[str, tuple[int]]:
    query = f"""SELECT
                MIN({PriceDataColNameInDB.TIMESTAMP}) AS {db_start_date}
            FROM 
                {shema_name}.{table_name}
            WHERE
                {PriceDataColNameInDB.PRICE_METADATA_ID} = %s;"""

    params = (price_metadata_id,)

    return query, params
