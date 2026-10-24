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
