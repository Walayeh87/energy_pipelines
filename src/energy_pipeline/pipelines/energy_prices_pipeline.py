import logging

from src.energy_pipeline.database.connection import create_db_engine, create_session
from src.energy_pipeline.database.data_upsertion import upsert_energy_prices_to_db
from src.energy_pipeline.ingestion.api_fetcher import fetch_data_from_api
from src.energy_pipeline.ingestion.url_creation import create_url_for_tomorrows_energy_prices
from src.energy_pipeline.preprocessing.energy_price import preprocess_energy_price
from utils.custom_objects import DbId
from utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def upload_daily_energy_price_to_db(
    bidding_zone: str,
    price_metadata_id: DbId,
) -> None:
    prices_url = create_url_for_tomorrows_energy_prices(bidding_zone=bidding_zone)
    prices_as_dict = fetch_data_from_api(url=prices_url)
    prices_as_df = preprocess_energy_price(prices_as_dict=prices_as_dict, price_metadata_id=price_metadata_id)

    db_engine = create_db_engine()
    session = create_session(db_engine=db_engine)

    upsert_energy_prices_to_db(session=session, prices=prices_as_df)


if __name__ == "__main__":
    upload_daily_energy_price_to_db(
        bidding_zone="DE-LU",
        price_metadata_id=DbId(value=1),
    )
