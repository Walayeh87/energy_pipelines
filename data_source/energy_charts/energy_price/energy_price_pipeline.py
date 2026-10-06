import logging

from data_source.data_fetcher_via_url import fetch_data
from data_source.energy_charts.energy_price.data_upsertion import upsert_df_to_db
from data_source.energy_charts.energy_price.price_col_name_in_db import (
    PriceDataColNameInDB,
)
from data_source.energy_charts.energy_price.processing import (
    process_fetched_energy_price_from_external_source,
)
from data_source.energy_charts.energy_price.query import create_upsert_sql_query
from data_source.energy_charts.energy_price.url_creation import (
    create_url_for_tomorrows_energy_prices,
)
from data_source.utilities.db_connector import establish_db_connection
from data_source.utilities.price_structure_in_db import PriceStructureInDB
from utils.logging_config import setup_logging
from utils.custom_objects import DbId

setup_logging()
logger = logging.getLogger(__name__)


def upload_daily_energy_price_to_db(
    bidding_zone: str,
    price_metadata_id: DbId,
    do_update_col: str = "energy_price",
) -> None:
    url = create_url_for_tomorrows_energy_prices(bidding_zone=bidding_zone)
    data_as_dict = fetch_data(url=url)
    df = process_fetched_energy_price_from_external_source(
        data_as_dict=data_as_dict, price_metadata_id=price_metadata_id
    )

    db_connection = establish_db_connection()

    table_cols = [
        PriceDataColNameInDB.TIMESTAMP,
        PriceDataColNameInDB.PRICE_METADATA_ID,
        PriceDataColNameInDB.ENERGY_PRICE,
    ]
    on_conflict_cols = [
        PriceDataColNameInDB.TIMESTAMP,
        PriceDataColNameInDB.PRICE_METADATA_ID,
    ]

    upsert_sql_query = create_upsert_sql_query(
        schema_name=PriceStructureInDB.SCHEMA_NAME,
        table_name=PriceStructureInDB.TABLE_NAME,
        table_cols=table_cols,
        on_conflict_cols=on_conflict_cols,
        do_update_col=do_update_col,
    )

    upsert_df_to_db(
        df=df, db_connection=db_connection, upsert_sql_query=upsert_sql_query
    )


if __name__ == "__main__":
    upload_daily_energy_price_to_db(
        bidding_zone="DE-LU",
        price_metadata_id=DbId(value=1),
    )
