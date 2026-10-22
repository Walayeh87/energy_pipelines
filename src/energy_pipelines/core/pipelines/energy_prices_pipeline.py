import logging

from pandas import Timedelta
from psycopg import OperationalError
from sqlalchemy.orm import Session

from energy_pipelines.core.database.connection import create_db_engine, create_db_session
from energy_pipelines.core.database.data_fetchers_from_db import (
    fetch_bidding_zone_and_price_metadata_id_as_mapper,
    fetch_price_metadata,
)
from energy_pipelines.core.database.data_upsertion import upsert_valid_energy_prices
from energy_pipelines.core.ingestion.api_fetcher import fetch_data_from_api
from energy_pipelines.core.ingestion.url_creation import create_url_for_tomorrows_energy_prices
from energy_pipelines.core.preprocessing.energy_price_preprocessing import preprocess_price_data
from energy_pipelines.core.validation.temp_schedule_validator import validate_energy_price
from energy_pipelines.utils.logging_config import setup_logging
from energy_pipelines.utils.time_constant import TimeConstant

setup_logging()
logger = logging.getLogger(__name__)


def daily_energy_price_pipeline(update_on_conflict: bool = False) -> None:
    db_engine = create_db_engine()
    session = create_db_session(db_engine=db_engine)

    mapper = fetch_bidding_zone_and_price_metadata_id_as_mapper(session=session)

    for bidding_zone, price_metadata_id in mapper.items():
        try:
            logger.info(f"Start daily upserting process for bidding zone '{bidding_zone}'.")
            _run_energy_price_pipeline(
                session=session,
                price_metadata_id=price_metadata_id,
                bidding_zone=bidding_zone,
                update_on_conflict=update_on_conflict,
            )

        except (ValueError, OperationalError, RuntimeError) as e:
            logger.exception(f"{type(e).__name__} occurred while upserting energy prices: {e}")

        except Exception as e:
            logger.exception(f"Unexpected error occurred while upserting energy prices: {e}")

    logger.info("Daily upserting process completed.")


def _run_energy_price_pipeline(
    session: Session,
    price_metadata_id: int,
    bidding_zone: str,
    update_on_conflict: bool,
) -> None:
    prices_url = create_url_for_tomorrows_energy_prices(bidding_zone=bidding_zone)
    prices_as_dict = fetch_data_from_api(url=prices_url)
    preprocessed_prices = preprocess_price_data(
        prices_as_dict=prices_as_dict,
        price_metadata_id=price_metadata_id,
    )
    price_metadata = fetch_price_metadata(session=session, metadata_id=price_metadata_id)
    expected_schedule_length = int(TimeConstant.SEC_IN_DAY / Timedelta(price_metadata.freq).total_seconds())
    validation_result = validate_energy_price(
        energy_price=preprocessed_prices,
        expected_length=expected_schedule_length,
    )
    if validation_result.is_valid:
        upsert_valid_energy_prices(
            session=session,
            prices=preprocessed_prices,
            update_on_conflict=update_on_conflict,
        )


if __name__ == "__main__":
    daily_energy_price_pipeline(update_on_conflict=False)
