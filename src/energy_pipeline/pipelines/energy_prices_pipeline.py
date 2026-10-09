import logging

from sqlalchemy.orm import Session

from src.energy_pipeline.database.connection import create_db_engine, create_session
from src.energy_pipeline.database.data_upsertion import upsert_energy_prices_to_db
from src.energy_pipeline.database.models import PriceMetadata, Regions
from src.energy_pipeline.ingestion.api_fetcher import fetch_data_from_api
from src.energy_pipeline.ingestion.url_creation import create_url_for_tomorrows_energy_prices
from src.energy_pipeline.preprocessing.energy_price import preprocess_energy_price
from utils.custom_objects import DbId
from utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def get_bidding_zone_and_price_metadata_ids_mapper(session: Session, bidding_zones: list[str]) -> dict[str, DbId]:
    mapper = {}
    for bidding_zone in bidding_zones:
        result = session.query(PriceMetadata.price_metadata_id).filter(PriceMetadata.bidding_zone == bidding_zone).all()
        if len(result) == 0:
            logger.warning(
                f"No price_metadata found for bidding zone: '{bidding_zone}'!"
                f" Daily prices will not be uploaded for this zone."
            )
        id_as_int = [price_metadata_id for (price_metadata_id,) in result][0] if result else 0
        mapper[bidding_zone] = DbId(id_as_int)
    return mapper


def get_bidding_zones(session: Session) -> list[str]:
    raw_result = session.query(Regions.bidding_zone).all()

    return [bidding_zone for (bidding_zone,) in raw_result]


def upload_daily_energy_price_to_db(update_on_conflict: bool = False) -> None:
    db_engine = create_db_engine()
    session = create_session(db_engine=db_engine)

    bidding_zones = get_bidding_zones(session=session)
    mapper = get_bidding_zone_and_price_metadata_ids_mapper(session=session, bidding_zones=bidding_zones)

    for bidding_zone, price_metadata_id in mapper.items():
        prices_url = create_url_for_tomorrows_energy_prices(bidding_zone=bidding_zone)
        prices_as_dict = fetch_data_from_api(url=prices_url)
        prices_as_df = preprocess_energy_price(prices_as_dict=prices_as_dict, price_metadata_id=price_metadata_id)
        upsert_energy_prices_to_db(session=session, prices=prices_as_df, update_on_conflict=update_on_conflict)


if __name__ == "__main__":
    upload_daily_energy_price_to_db(update_on_conflict=False)
