import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from psycopg import OperationalError
from sqlalchemy.orm import Session

from energy_pipelines.core.config.settings import DB_URL
from energy_pipelines.core.database.connection import create_db_engine, create_db_session
from energy_pipelines.core.database.data_fetchers_from_db import (
    fetch_bidding_zone_and_price_metadata_id_as_mapper,
)
from energy_pipelines.core.database.data_upsertion import upsert_energy_prices, upsert_price_fetching_failures
from energy_pipelines.core.ingestion.api_fetcher import fetch_data_from_api
from energy_pipelines.core.ingestion.url_creation import create_url_for_tomorrows_energy_prices
from energy_pipelines.core.preprocessing.energy_price_preprocessing import (
    preprocess_price_data,
    preprocess_price_fetching_failures,
)
from energy_pipelines.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def energy_price_pipeline(db_url: str, update_on_conflict: bool = False) -> None:
    db_engine = create_db_engine(db_url=db_url)

    try:
        with create_db_session(db_engine=db_engine) as session:
            _run_energy_price_pipeline(session=session, update_on_conflict=update_on_conflict)
    finally:
        db_engine.dispose()


def _run_energy_price_pipeline(session: Session, update_on_conflict: bool) -> None:
    mapper = fetch_bidding_zone_and_price_metadata_id_as_mapper(session=session)

    for bidding_zone, price_metadata_id in mapper.items():
        try:
            logger.info(f"Start daily upserting process for bidding zone '{bidding_zone}'.")
            _run_bidding_zone_pipeline(
                session=session,
                price_metadata_id=price_metadata_id,
                bidding_zone=bidding_zone,
                update_on_conflict=update_on_conflict,
            )

        except (ValueError, OperationalError) as e:
            logger.exception(f"{type(e).__name__} occurred while upserting energy prices: {e}")

        except Exception as e:
            logger.exception(f"Unexpected error occurred while upserting energy prices: {e}")

    logger.info("Daily upserting process completed.")


def _run_bidding_zone_pipeline(
    session: Session,
    price_metadata_id: int,
    bidding_zone: str,
    update_on_conflict: bool,
) -> None:
    prices_url = create_url_for_tomorrows_energy_prices(bidding_zone=bidding_zone)
    fetching_result = fetch_data_from_api(url=prices_url)

    successful_http_response_status_code = 200
    if fetching_result.http_response_status_code == successful_http_response_status_code:
        preprocessed_prices = preprocess_price_data(
            prices_as_dict=fetching_result.data_as_dict,
            price_metadata_id=price_metadata_id,
        )
        upsert_energy_prices(
            session=session,
            prices=preprocessed_prices,
            update_on_conflict=update_on_conflict,
        )
    else:
        logger.warning(
            f"Failed to fetch energy prices for bidding zone '{bidding_zone}'"
            f" and price metadata ID {price_metadata_id}."
        )
        preprocessed_price_fetching_failures = preprocess_price_fetching_failures(
            price_metadata_id=price_metadata_id,
            http_response_status_code=fetching_result.http_response_status_code,
            recording_time=datetime.now(tz=ZoneInfo("UTC")),
            error_msg=fetching_result.error_msg,
        )
        upsert_price_fetching_failures(
            session=session,
            price_fetching_failures=preprocessed_price_fetching_failures,
        )


def main() -> None:
    setup_logging()
    energy_price_pipeline(db_url=DB_URL, update_on_conflict=False)


if __name__ == "__main__":
    main()
