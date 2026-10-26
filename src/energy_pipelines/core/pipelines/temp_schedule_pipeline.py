from typing import Literal

from energy_pipelines.core.config.settings import DB_URL
from energy_pipelines.core.database.connection import create_db_engine, create_db_session
from energy_pipelines.core.pipeline_runners.temp_schedule_pipeline_runner import run_temp_schedule_pipeline
from energy_pipelines.utils.logging_config import setup_logging


def temp_schedule_pipeline(
    db_url: str,
    site_ids: list[int] | int | Literal["all_site_ids"],
    update_on_conflict: bool = False,
) -> None:
    """Generate and store temperature schedules for configured sites.

    1- Retrieves the required site configuration and energy price data from DB.
    2- generates temperature schedules using the configured algorithms (one site can have
     more than 1 algorithm).
    Note: if energy prices are not available, backup schedules are generated.
    3- validates the results.
    4- upserts them into the database according to the configured conflict-handling policy. Failures are
     recorded for later inspection.

    Checkout run_temp_schedule_pipeline for more information about the logic of this pipeline.

    This function builds a database engine, opens a session, runs the pipeline logic,
    and ensures the engine is properly disposed in all cases.

    Args:
        db_url: The database connection string to use for creating the SQLAlchemy engine.
        site_ids: The site(s) to process. This may be:
            - a single integer site ID,
            - a list of integer site IDs,
            - or the special literal "all_site_ids" to process all sites.
        update_on_conflict: If True, existing records will be updated when conflicts occur.
            If False, conflicting updates are skipped.

    Returns:
        None
    """
    db_engine = create_db_engine(db_url=db_url)

    try:
        with create_db_session(db_engine=db_engine) as session:
            run_temp_schedule_pipeline(
                session=session,
                site_ids=site_ids,
                update_on_conflict=update_on_conflict,
            )
    finally:
        db_engine.dispose()


def main() -> None:
    setup_logging()

    temp_schedule_pipeline(db_url=DB_URL, site_ids="all_site_ids", update_on_conflict=False)
    # The SITE_MAPPER can be used to provide the site IDs in a user-friendly way.
    # from energy_pipelines.core.config.manual_mappers import SITE_MAPPER
    #
    # temp_schedule_pipeline(db_url=DB_URL, site_ids=[SITE_MAPPER["First Site"]])


if __name__ == "__main__":
    main()
