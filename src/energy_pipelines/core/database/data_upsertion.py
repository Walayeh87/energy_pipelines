import logging

from pandas import DataFrame
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from energy_pipelines.core.database.table_models import (
    AlgosOutput,
    FailingAlgosOutput,
    PriceData,
    PriceFetchingFailures,
)

logger = logging.getLogger(__name__)


def upsert_energy_prices(session: Session, prices: DataFrame, update_on_conflict: bool) -> None:
    try:
        stmt = insert(PriceData).values(prices.to_dict(orient="records"))
        cols2exclude_as_mapper = {
            column.name: stmt.excluded[column.name]
            for column in PriceData.__table__.columns
            if not column.primary_key
        }

        if update_on_conflict:
            stmt = stmt.on_conflict_do_update(
                index_elements=[PriceData.timestamp.key, PriceData.price_metadata_id.key],
                set_=cols2exclude_as_mapper,
            )
            logger.info("Energy prices have been upserted with updates.")

        else:
            stmt = stmt.on_conflict_do_nothing(
                index_elements=[PriceData.timestamp.key, PriceData.price_metadata_id.key]
            )
            logger.info("Energy prices have been upserted without updates.")

        session.execute(stmt)
        session.commit()

    except Exception:
        session.rollback()
        raise


def upsert_price_fetching_failures(
    session: Session,
    price_fetching_failures: DataFrame,
) -> None:
    try:
        stmt = insert(PriceFetchingFailures).values(price_fetching_failures.to_dict(orient="records"))

        session.execute(stmt)
        session.commit()

    except Exception:
        session.rollback()
        raise

    logger.info("Price fetching failures have been upserted successfully.")


def upsert_valid_temp_schedule(
    session: Session,
    temp_schedule: DataFrame,
    update_on_conflict: bool,
) -> None:
    try:
        stmt = insert(AlgosOutput).values(temp_schedule.to_dict(orient="records"))
        cols2exclude_as_mapper = {
            column.name: stmt.excluded[column.name]
            for column in AlgosOutput.__table__.columns
            if not column.primary_key
        }

        if update_on_conflict:
            stmt = stmt.on_conflict_do_update(
                index_elements=[AlgosOutput.timestamp.key, AlgosOutput.site_id.key, AlgosOutput.algo_id.key],
                set_=cols2exclude_as_mapper,
            )
        else:
            stmt = stmt.on_conflict_do_nothing(
                index_elements=[AlgosOutput.timestamp.key, AlgosOutput.site_id.key, AlgosOutput.algo_id.key]
            )

        session.execute(stmt)
        session.commit()

    except Exception:
        session.rollback()
        raise


def upsert_failing_temp_schedule(
    session: Session,
    preprocessed_failing_algos_output: DataFrame,
) -> None:
    try:
        stmt = insert(FailingAlgosOutput).values(preprocessed_failing_algos_output.to_dict(orient="records"))

        session.execute(stmt)
        session.commit()

    except Exception:
        session.rollback()
        raise

    logger.info("Failing temperature schedule values have been upserted successfully.")
