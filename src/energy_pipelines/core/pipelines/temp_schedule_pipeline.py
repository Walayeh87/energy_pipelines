import logging

from pandas import Timedelta

from energy_pipelines.core.database.connection import create_db_engine, create_db_session
from energy_pipelines.core.database.data_fetchers_from_db import (
    fetch_all_site_ids,
    fetch_all_site_names,
    fetch_bidding_zone_and_price_metadata_id_as_mapper,
    fetch_cooling_specs,
    fetch_dt_data,
    fetch_site_bidding_zone,
    fetch_site_name_and_id_as_mapper,
)
from energy_pipelines.core.database.models import CoolingSpecs, PriceData, SchemaNames, Site
from energy_pipelines.core.processing.energy_price_processing import process_energy_price_data
from energy_pipelines.utils.logging_config import setup_logging
from energy_pipelines.utils.time_helpers import get_tomorrows_date

setup_logging()
logger = logging.getLogger(__name__)


def upsert_temp_schedule(site_names: list[str] | str = "all") -> None:
    db_engine = create_db_engine()
    session = create_db_session(db_engine=db_engine)

    all_site_names = fetch_all_site_names(session=session)

    if isinstance(site_names, str) and site_names != "all":
        site_names = [site_names]

    if isinstance(site_names, str) and site_names == "all":
        site_names = all_site_names

    for site_name in site_names:
        if site_name not in all_site_names:
            logger.warning(
                f"Site '{site_name}' is not in stored in table '{SchemaNames.SITES}.{Site.__tablename__}'."
                f" Sites in the DB: {all_site_names}."
                f" No temperature schedule created for this site."
            )
            continue

        logger.info(f"Start temperature schedule upsertion process for site '{site_name}'.")

        site_name_and_id_mapper = fetch_site_name_and_id_as_mapper(session=session)
        site_id = site_name_and_id_mapper[site_name]

        site_ids_in_cooling_specs = fetch_all_site_ids(session=session, table=CoolingSpecs)
        if site_id not in site_ids_in_cooling_specs:
            logger.warning(
                f"No temperature schedule will be created for site '{site_name}',"
                f" since there is no corresponding site_id {site_id} found in table"
                f" '{SchemaNames.SITES}.{CoolingSpecs.__tablename__}'."
            )
            continue

        site_bidding_zone = fetch_site_bidding_zone(session=session, site_id=site_id)
        bidding_zone_and_data_id_as_mapper = fetch_bidding_zone_and_price_metadata_id_as_mapper(
            session=session, bidding_zones=site_bidding_zone
        )
        data_id = bidding_zone_and_data_id_as_mapper[site_bidding_zone]

        energy_price_fetching_result = fetch_dt_data(
            session=session,
            cols2fetch=[PriceData.timestamp, PriceData.energy_price],
            data_id=data_id,
            start=get_tomorrows_date(),
            end=get_tomorrows_date() + Timedelta(days=1),
        )

        energy_price_processing_result = process_energy_price_data(
            session=session, fetching_result=energy_price_fetching_result
        )

        if energy_price_processing_result.processed_prices.empty:
            logger.warning(
                f"No temperature schedule will be created for site '{site_name}', since there is no "
                f"energy price available."
            )
            continue

        cooling_specs_fetching_result = fetch_cooling_specs(session=session, site_id=site_id)

    logger.info("Temperature schedule upsertion process has been completed.")

    # return energy_price_processing_result


if __name__ == "__main__":
    result = upsert_temp_schedule("all")
