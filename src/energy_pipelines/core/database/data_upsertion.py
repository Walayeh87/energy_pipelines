import logging
from typing import Any

from pandas import DataFrame
from sqlalchemy import FromClause, exists, select, tuple_
from sqlalchemy.dialects.postgresql import Insert, insert
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from energy_pipelines.core.database.table_models import (
    AlgosOutput,
    FailingAlgosOutput,
    PriceData,
    PriceFetchingFailures,
)

logger = logging.getLogger(__name__)


def upsert_energy_prices(session: Session, prices: DataFrame, update_on_conflict: bool) -> None:
    stmt = insert(PriceData).values(prices.to_dict(orient="records"))

    try:
        records_exist = _check_records_existence(
            session=session,
            table=PriceData.__table__,
            primary_keys=[PriceData.timestamp.key, PriceData.price_metadata_id.key],
            primary_values=list(
                zip(
                    prices[PriceData.timestamp.key].tolist(),
                    prices[PriceData.price_metadata_id.key].tolist(),
                    strict=True,
                )
            ),
        )

    except OperationalError:
        session.rollback()
        raise

    if records_exist:
        logger.info("Some/all energy prices already exist in the database.")

    cols2exclude_as_mapper = {
        column.name: stmt.excluded[column.name]
        for column in PriceData.__table__.columns
        if not column.primary_key
    }

    stmt = _handle_upsertion_policy(
        stmt=stmt,
        records2insert=prices,
        records_exist=records_exist,
        primary_keys=[PriceData.timestamp.key, PriceData.price_metadata_id.key],
        cols2exclude_as_mapper=cols2exclude_as_mapper,
        update_on_conflict=update_on_conflict,
    )

    try:
        session.execute(stmt)
        session.commit()
    except OperationalError:
        session.rollback()
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError("An error occurred while trying to upsert energy prices.") from e


def upsert_price_fetching_failures(
    session: Session,
    price_fetching_failures: DataFrame,
) -> None:
    stmt = insert(PriceFetchingFailures).values(price_fetching_failures.to_dict(orient="records"))

    try:
        session.execute(stmt)
        session.commit()
    except OperationalError:
        session.rollback()
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError("An error occurred while trying to upsert price fetching failures.") from e

    logger.info("Price fetching failures have been upserted successfully.")


def upsert_valid_temp_schedule(
    session: Session,
    temp_schedule: DataFrame,
    update_on_conflict: bool,
) -> None:
    stmt = insert(AlgosOutput).values(temp_schedule.to_dict(orient="records"))

    try:
        records_exist = _check_records_existence(
            session=session,
            table=AlgosOutput.__table__,
            primary_keys=[AlgosOutput.timestamp.key, AlgosOutput.site_id.key, AlgosOutput.algo_id.key],
            primary_values=list(
                zip(
                    temp_schedule[AlgosOutput.timestamp.key].tolist(),
                    temp_schedule[AlgosOutput.site_id.key].tolist(),
                    temp_schedule[AlgosOutput.algo_id.key].tolist(),
                    strict=True,
                )
            ),
        )
    except OperationalError:
        session.rollback()
        raise

    if records_exist:
        logger.info("Some/all temperature schedule values already exist in the database.")

    cols2exclude_as_mapper = {
        column.name: stmt.excluded[column.name]
        for column in AlgosOutput.__table__.columns
        if not column.primary_key
    }
    stmt = _handle_upsertion_policy(
        stmt=stmt,
        records2insert=temp_schedule,
        records_exist=records_exist,
        primary_keys=[AlgosOutput.timestamp.key, AlgosOutput.site_id.key, AlgosOutput.algo_id.key],
        cols2exclude_as_mapper=cols2exclude_as_mapper,
        update_on_conflict=update_on_conflict,
    )

    try:
        session.execute(stmt)
        session.commit()
    except OperationalError:
        session.rollback()
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError("An error occurred while trying to upsert temperature schedule.") from e


def upsert_failing_temp_schedule(
    session: Session,
    preprocessed_failing_algos_output: DataFrame,
) -> None:
    stmt = insert(FailingAlgosOutput).values(preprocessed_failing_algos_output.to_dict(orient="records"))

    try:
        session.execute(stmt)
        session.commit()
    except OperationalError:
        session.rollback()
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError("An error occurred while trying to upsert failing temperature schedule.") from e

    logger.info("Failing temperature schedule values have been upserted successfully.")


def _check_records_existence(
    session: Session,
    table: FromClause,
    primary_keys: list[str],
    primary_values: list[tuple[Any, ...]],
) -> bool:
    if not primary_values:
        return False

    columns = [table.c[column] for column in primary_keys]

    stmt = select(exists().where(tuple_(*columns).in_(primary_values)))

    return bool(session.scalar(stmt))


def _handle_upsertion_policy(
    stmt: Insert,
    records2insert: DataFrame,
    records_exist: bool,
    primary_keys: list[str],
    cols2exclude_as_mapper: dict[str, Any],
    update_on_conflict: bool,
) -> Insert:
    if update_on_conflict:
        stmt = stmt.on_conflict_do_update(index_elements=primary_keys, set_=cols2exclude_as_mapper)

        if records_exist:
            logger.info(f"{len(records2insert)} rows will be updated in the database.")
        else:
            logger.info(f"{len(records2insert)} rows will be upserted into the database.")
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=primary_keys)

        if records_exist:
            logger.info(
                "No data will be upserted to the DB since they are already exist."
                " If you want to update them, set the parameter 'update_on_conflict' to True."
            )
        else:
            logger.info(f"{len(records2insert)} rows will be upserted into the database.")

    return stmt
