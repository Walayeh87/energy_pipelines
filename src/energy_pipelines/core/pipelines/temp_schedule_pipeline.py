import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal
from zoneinfo import ZoneInfoNotFoundError

from pandas import Series, Timedelta
from pandas.core.frame import DataFrame
from sqlalchemy.orm import Session

from energy_pipelines.core.algos.temp_schedule_creator import (
    create_backup_temp_schedule,
    create_temp_schedule,
)
from energy_pipelines.core.database.connection import create_db_engine, create_db_session
from energy_pipelines.core.database.data_fetchers_from_db import (
    fetch_algo_name,
    fetch_all_site_ids_in_site_algos,
    fetch_energy_price_data,
    fetch_price_metadata,
    fetch_price_metadata_id_by_bidding_zone,
    fetch_site,
    fetch_site_algos,
    fetch_site_names_by_ids,
)
from energy_pipelines.core.database.data_upsertion import upsert_valid_temp_schedule
from energy_pipelines.core.database.param_models import (
    ALGO_MODEL_MAPPER,
    TempScheduleCreatorParams,
)
from energy_pipelines.core.database.table_models import PriceData, SchemaNames, Site
from energy_pipelines.core.preprocessing.temp_schedule_preprocessing import (
    preprocess_temp_schedule,
)
from energy_pipelines.core.processing.energy_price_processing import (
    ProcessingIssues,
    process_energy_price_data,
)
from energy_pipelines.core.validation.temp_schedule_validator import (
    TempScheduleValidationResult,
    validate_backup_temp_schedule,
    validate_temp_schedule,
)
from energy_pipelines.utils.custom_errors import EmptyTableError, TempSchedulePipelineError
from energy_pipelines.utils.logging_config import setup_logging
from energy_pipelines.utils.time_constant import TimeConstant
from energy_pipelines.utils.time_helpers import get_tomorrows_date, get_tz_diff_in_h

setup_logging()
logger = logging.getLogger(__name__)


class SitePipelineStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    INACTIVED_ALGO = "inactive_algo"


@dataclass
class SitePipelineResult:
    site_id: int
    algo_id: int
    status: SitePipelineStatus
    schedule_validation_result: TempScheduleValidationResult | None = None
    temp_schedule: DataFrame | None = None
    is_backup_schedule: bool | None = None

    # The output of EnergyPriceProcessingResult
    original_prices: DataFrame | None = None
    processed_prices: DataFrame | None = None

    mask_of_filled_values: Series | None = None
    processing_issue: ProcessingIssues | None = None


ALL_SITE_IDS = Literal["all_site_ids"]


def temp_schedule_pipeline(
    site_ids: list[int] | int | ALL_SITE_IDS = "all_site_ids",
    update_on_conflict: bool = False,
) -> None:
    db_engine = create_db_engine()
    session = create_db_session(db_engine=db_engine)

    all_site_ids = fetch_all_site_ids_in_site_algos(session=session)

    if isinstance(site_ids, str) and site_ids != ALL_SITE_IDS.__args__[0]:
        raise ValueError(f"Invalid site_ids provided: {site_ids}")

    if isinstance(site_ids, str) and site_ids == ALL_SITE_IDS.__args__[0]:
        site_ids = all_site_ids

    if isinstance(site_ids, int):
        site_ids = [site_ids]

    for site_id in site_ids:
        if site_id not in all_site_ids:
            logger.warning(
                f"site_id: {site_id} not found in '{SchemaNames.SITES}.{Site.__tablename__}'."
                f" No schedule will be created for this site."
            )

    site_names = fetch_site_names_by_ids(session=session, site_ids=site_ids)

    if len(site_names) == 0:
        logger.warning(
            f"All provided site_ids: {site_ids} not found in '{SchemaNames.SITES}.{Site.__tablename__}'."
        )
        return

    failed_sites = []
    for site_name in site_names:
        logger.info(f"Start temperature schedule upsertion process for site '{site_name}'.")
        try:
            site_pipeline_result = _run_site_pipeline(
                session=session,
                site_name=site_name,
                update_on_conflict=update_on_conflict,
            )

        except (ValueError, EmptyTableError, ZoneInfoNotFoundError) as e:
            logger.exception(
                f"{type(e).__name__} occurred while creating a schedule for site '{site_name}': {e}"
            )
            failed_sites.append(site_name)

        except Exception as e:
            logger.exception(
                f"Unexpected error occurred while creating a schedule for site '{site_name}': {e}"
            )
            failed_sites.append(site_name)

    if failed_sites:
        logger.warning(f"Failed to create temperature schedules for the site(s): {failed_sites}")

    logger.info("Temperature schedule process has been completed.")

    # return energy_price_processing_result


def _run_site_pipeline(session: Session, site_name: str, update_on_conflict: bool) -> SitePipelineResult:
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
            return SitePipelineResult(
                site_id=site.id,
                algo_id=site_algo.algo_id,
                status=SitePipelineStatus.INACTIVED_ALGO,
            )

        price_metadata_id = fetch_price_metadata_id_by_bidding_zone(
            session=session,
            bidding_zone=site.bidding_zone,
        )

        tz_diff_in_h = get_tz_diff_in_h(target_tz=site.tz)
        start = get_tomorrows_date(tz="UTC") + Timedelta(hours=tz_diff_in_h)
        end = start + Timedelta(days=1)
        energy_price_fetching_result = fetch_energy_price_data(
            session=session,
            cols2fetch=[PriceData.timestamp, PriceData.energy_price],
            price_metadata_id=price_metadata_id,
            start=start,
            end=end,
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

        expected_schedule_length = int(TimeConstant.SEC_IN_DAY / Timedelta(algo_params.freq).total_seconds())

        energy_prices_not_available = (
            energy_price_processing_result.processing_issue == ProcessingIssues.EMPTY_DATA
        )
        have_unknown_issues = energy_price_processing_result.processing_issue == ProcessingIssues.UNKNOWN
        if algo_model == TempScheduleCreatorParams:
            if energy_prices_not_available or have_unknown_issues:
                backup_temp_schedule = create_backup_temp_schedule(
                    algo_freq=algo_params.freq,
                    default_temp=algo_params.temps["default_temp"],
                    tz="UTC",
                )
                logger.warning(
                    f"Default temperature schedule of constant: {algo_params.temps['default_temp']}"
                    f" °C is created for site '{site.name}' with algo '{algo_name}', since there is"
                    f" no energy price available."
                )
                preprocessed_temp_schedule = preprocess_temp_schedule(
                    temp_schedule=backup_temp_schedule,
                    site_id=site.id,
                    algo_id=site_algo.algo_id,
                )
                validation_result = validate_backup_temp_schedule(
                    temp_schedule=preprocessed_temp_schedule,
                    expected_length=expected_schedule_length,
                    default_temp=algo_params.temps["default_temp"],
                )
                upsert_valid_temp_schedule(
                    session=session,
                    temp_schedule=preprocessed_temp_schedule,
                    update_on_conflict=update_on_conflict,
                )
                return SitePipelineResult(
                    site_id=site.id,
                    algo_id=site_algo.algo_id,
                    temp_schedule=preprocessed_temp_schedule,
                    schedule_validation_result=validation_result,
                    status=SitePipelineStatus.SUCCESS,
                    is_backup_schedule=True,
                    original_prices=energy_price_processing_result.original_prices,
                    processed_prices=energy_price_processing_result.processed_prices,
                    mask_of_filled_values=energy_price_processing_result.mask_of_filled_values,
                    processing_issue=energy_price_processing_result.processing_issue,
                )

        if algo_model == TempScheduleCreatorParams:
            temp_schedule = create_temp_schedule(
                prices=energy_price_processing_result.processed_prices,
                min_temp=algo_params.temps["min_temp"],
                max_temp=algo_params.temps["max_temp"],
                default_temp=algo_params.temps["default_temp"],
            )
            logger.info(f"Temperature schedule for site '{site.name}' with algo '{algo_name}' is created.")
            preprocessed_temp_schedule = preprocess_temp_schedule(
                temp_schedule=temp_schedule,
                site_id=site.id,
                algo_id=site_algo.algo_id,
            )
            validation_result = validate_temp_schedule(
                temp_schedule=preprocessed_temp_schedule,
                expected_length=expected_schedule_length,
                min_temp=algo_params.temps["min_temp"],
                max_temp=algo_params.temps["max_temp"],
            )
            upsert_valid_temp_schedule(
                session=session,
                temp_schedule=preprocessed_temp_schedule,
                update_on_conflict=update_on_conflict,
            )
            return SitePipelineResult(
                site_id=site.id,
                algo_id=site_algo.algo_id,
                temp_schedule=temp_schedule,
                schedule_validation_result=validation_result,
                status=SitePipelineStatus.SUCCESS,
                is_backup_schedule=False,
                original_prices=energy_price_processing_result.original_prices,
                processed_prices=energy_price_processing_result.processed_prices,
                mask_of_filled_values=energy_price_processing_result.mask_of_filled_values,
                processing_issue=energy_price_processing_result.processing_issue,
            )

        else:
            logger.warning(f"The algo model: '{algo_model}' is not available.")

    raise TempSchedulePipelineError("Could not run a pipeline due to an unexpected error.")


if __name__ == "__main__":
    result = temp_schedule_pipeline("all_site_ids")
