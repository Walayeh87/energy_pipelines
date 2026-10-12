import logging

from energy_pipelines.core.database.connection import create_db_engine, create_session
from energy_pipelines.core.database.data_fetchers_from_db import (
    fetch_bidding_zone_and_price_metadata_ids_mapper,
    fetch_bidding_zones,
)
from energy_pipelines.core.database.data_upsertion import upsert_energy_prices_to_db
from energy_pipelines.core.ingestion.api_fetcher import fetch_data_from_api
from energy_pipelines.core.ingestion.url_creation import create_url_for_tomorrows_energy_prices
from energy_pipelines.core.preprocessing.energy_price_preprocessing import preprocess_energy_price
from energy_pipelines.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def upsert_daily_energy_price(update_on_conflict: bool = False) -> None:
    db_engine = create_db_engine()
    session = create_session(db_engine=db_engine)

    bidding_zones = fetch_bidding_zones(session=session)
    mapper = fetch_bidding_zone_and_price_metadata_ids_mapper(session=session, bidding_zones=bidding_zones)

    for bidding_zone, price_metadata_id in mapper.items():
        if price_metadata_id <= 0:
            logger.warning(
                f"No price_metadata found for bidding zone: '{bidding_zone}'!"
                f" Daily energy prices will not be upserted for this zone."
            )
            continue

        logger.info(f"Start daily upserting process for bidding zone '{bidding_zone}'.")

        prices_url = create_url_for_tomorrows_energy_prices(bidding_zone=bidding_zone)
        prices_as_dict = fetch_data_from_api(url=prices_url)
        prices_as_df = preprocess_energy_price(
            prices_as_dict=prices_as_dict, price_metadata_id=price_metadata_id
        )
        upsert_energy_prices_to_db(
            session=session, prices=prices_as_df, update_on_conflict=update_on_conflict
        )

    logger.info("Daily upserting process completed.")


if __name__ == "__main__":
    upsert_daily_energy_price(update_on_conflict=False)
