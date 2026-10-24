from energy_pipelines.core.config.settings import DB_URL
from energy_pipelines.core.database.connection import create_db_engine, create_db_session
from energy_pipelines.core.pipeline_runners.energy_prices_pipeline_runner import run_energy_price_pipeline
from energy_pipelines.utils.logging_config import setup_logging


def energy_price_pipeline(db_url: str, update_on_conflict: bool = False) -> None:
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
