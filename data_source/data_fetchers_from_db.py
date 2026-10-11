import logging
from datetime import datetime

import psycopg
import pytz
from fastapi import FastAPI, HTTPException

from data_source.db.energy_price.queries import (
    create_energy_price_fetching_query,
    create_query_for_earliest_timestamp,
)
from data_source.utilities.db_connector import establish_db_connection
from data_source.utilities.price_structure_in_db import PriceStructureInDB
from energy_pipelines.utils.time_helpers.helpers import get_current_date

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
def root() -> dict:
    return {"message": "DB API is running"}


@app.get("/energy_prices")
def fetch_energy_prices(
    price_metadata_id: int,
    start_date: datetime,
    end_date: datetime,
) -> list[dict]:
    if price_metadata_id <= 0:
        logger.error("price_metadata_id must be greater than 0")
        raise ValueError

    if start_date >= end_date:
        logger.error("start_date must not be after end_date")
        raise ValueError

    if end_date > get_current_date():
        logger.error("index must not contain future dates")
        raise ValueError

    earliest_timestamp_in_db = fetch_earliest_timestamp_in_table(
        price_metadata_id=price_metadata_id,
        shema_name=PriceStructureInDB.SCHEMA_NAME,
        table_name=PriceStructureInDB.TABLE_NAME,
    )

    if start_date < earliest_timestamp_in_db:
        logger.error(
            f"The historical data provided starts before the earliest timestamp in energy prices for price_metadata_id"
            f" {price_metadata_id}."
        )
        raise ValueError

    query, params = create_energy_price_fetching_query(
        price_metadata_id=price_metadata_id,
        start_date=start_date,
        end_date=end_date,
    )

    try:
        with establish_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()

        return result

    except psycopg.Error as e:
        raise HTTPException(status_code=500, detail="Database error") from e


@app.get("/energy_prices")
def fetch_earliest_timestamp_in_table(price_metadata_id: int, shema_name: str, table_name: str) -> datetime:
    db_start_date = "db_start_date"  # custom name

    query, params = create_query_for_earliest_timestamp(
        db_start_date=db_start_date,
        shema_name=shema_name,
        table_name=table_name,
        price_metadata_id=price_metadata_id,
    )

    try:
        with establish_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()[0].get(db_start_date)

        return result

    except psycopg.Error as e:
        raise HTTPException(status_code=500, detail="Database error") from e


if __name__ == "__main__":
    result = fetch_energy_prices(
        price_metadata_id=1,
        start_date=datetime(year=2026, month=6, day=1, tzinfo=pytz.UTC),
        end_date=datetime(year=2026, month=6, day=5, tzinfo=pytz.UTC),
    )
