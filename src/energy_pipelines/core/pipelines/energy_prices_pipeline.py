from energy_pipelines.core.config.settings import DB_URL
from energy_pipelines.core.database.connection import create_db_engine, create_db_session
from energy_pipelines.core.pipeline_runners.energy_prices_pipeline_runner import run_energy_price_pipeline
from energy_pipelines.utils.logging_config import setup_logging


def energy_price_pipeline(db_url: str, update_on_conflict: bool = False) -> None:
    """Fetch from an external API, process, and store energy price data in DB.

    1- Retrieves energy price data from the external API.
    2- processes and validates the records.
    3- upserts them into the database according to the configured conflict-handling policy.

    Checkout run_energy_price_pipeline for more information about the logic of this pipeline.

    Args:
        db_url: Database connection URL used to create the SQLAlchemy engine.
        update_on_conflict: Whether to update existing records when a conflict is detected
            during the pipeline execution.

    Returns:
        None: The function performs side effects by running the pipeline and does not return
        any value.
    """
    db_engine = create_db_engine(db_url=db_url)

    try:
        with create_db_session(db_engine=db_engine) as session:
            run_energy_price_pipeline(session=session, update_on_conflict=update_on_conflict)
    finally:
        db_engine.dispose()


def main() -> None:
    setup_logging()
    energy_price_pipeline(db_url=DB_URL, update_on_conflict=False)


if __name__ == "__main__":
    main()
