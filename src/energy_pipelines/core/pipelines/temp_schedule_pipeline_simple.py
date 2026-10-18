import logging

from pandas import Timedelta
from sqlalchemy.orm import Session

from energy_pipelines.core.algos.temp_schedule_creator import create_backup_temp_schedule
from energy_pipelines.core.database.connection import create_db_engine, create_db_session
from energy_pipelines.core.database.data_fetchers_from_db import (
    fetch_algo_name,
    fetch_all_site_names,
    fetch_data_id_by_bidding_zone,
    fetch_energy_price_data,
    fetch_price_metadata,
    fetch_site,
    fetch_site_algos,
)
from energy_pipelines.core.database.models import PriceData
from energy_pipelines.core.database.param_models import (
    ALGO_MODEL_MAPPER,
    AdvancedTempScheduleCreatorParams,
    TempScheduleCreatorParams,
)
from energy_pipelines.core.processing.energy_price_processing import process_energy_price_data
from energy_pipelines.utils.custom_errors import EmptyTableError
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

    failed_sites = []
    for site_name in site_names:
        logger.info(f"Start temperature schedule upsertion process for site '{site_name}'.")
        try:
            site_pipeline_result = _run_site_pipeline(session=session, site_name=site_name)
        except ValueError as e:
            logger.exception(f"ValueError occurred while creating a schedule for site '{site_name}': {e}")
            failed_sites.append(site_name)

        except EmptyTableError as e:
            logger.exception(
                f"EmptyTableError occurred while creating a schedule for site '{site_name}': {e}"
            )
            failed_sites.append(site_name)

        except Exception as e:
            logger.exception(
                f"Unexpected error occurred while creating a schedule for site '{site_name}': {e}"
            )
            failed_sites.append(site_name)

    if failed_sites:
        logger.warning(f"The following site(s) failed to create temperature schedules: {failed_sites}")

    logger.info("Temperature schedule process has been completed.")

    # return energy_price_processing_result


def _run_site_pipeline(session: Session, site_name: str):
    site = fetch_site(session=session, site_name=site_name)
    site_algos = fetch_site_algos(session=session, site_id=site.id)  # A site could have multiple algos

    for site_algo in site_algos:
        algo_name = fetch_algo_name(session=session, algo_id=site_algo.algo_id)
        algo_model = ALGO_MODEL_MAPPER.get(site_algo.algo_id)
        algo_params = algo_model.model_validate(site_algo.params)

        if not site_algo.is_active:
            logger.warning(
                f"No temperature schedule will be created for site '{site.name}' with algo '{algo_name}',"
                f" since the algo is deactivated."
            )
            pass

        data_id = fetch_data_id_by_bidding_zone(session=session, bidding_zone=site.bidding_zone)

        energy_price_fetching_result = fetch_energy_price_data(
            session=session,
            cols2fetch=[PriceData.timestamp, PriceData.energy_price],
            price_metadata_id=data_id,
            start=get_tomorrows_date(),
            end=get_tomorrows_date() + Timedelta(days=1),
        )

        price_metadata = fetch_price_metadata(
            session=session,
            metadata_id=energy_price_fetching_result.price_metadata_id,
        )

        energy_price_processing_result = process_energy_price_data(
            fetching_result=energy_price_fetching_result,
            price_tz=price_metadata.tz,
            price_freq=price_metadata.freq,
        )

        energy_prices_not_available = energy_price_processing_result.processing_issue.EMPTY_DATA
        have_unknown_issues = energy_price_processing_result.processing_issue.UNKNOWN
        if (algo_model == TempScheduleCreatorParams) or (algo_model == AdvancedTempScheduleCreatorParams):
            if energy_prices_not_available or have_unknown_issues:
                logger.warning(
                    f"Default temperature schedule of constant: {algo_params.temps['default_temp']}"
                    f" °C will be created for site '{site.name}' with algo '{algo_name}', since there is"
                    f" no energy price available."
                )
                backup_temp_schedule = create_backup_temp_schedule(
                    algo_freq=algo_params.freq,
                    default_temp=algo_params.temps["default_temp"],
                    tz=site.tz,
                )
                pass

        if algo_model == TempScheduleCreatorParams:
            pass
            # handle the general case
        if algo_model == AdvancedTempScheduleCreatorParams:
            logger.warning("The advanced temperature schedule creator is not implemented yet!")
            pass
        else:
            logger.warning(f"The algo model: '{algo_model}' is not available.")


if __name__ == "__main__":
    result = upsert_temp_schedule("all")
