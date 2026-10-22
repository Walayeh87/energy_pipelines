import logging
from datetime import datetime
from typing import Any

from pandas import DataFrame, Series
from psycopg import OperationalError
from sqlalchemy import exists, select, tuple_
from sqlalchemy.dialects.postgresql import Insert, insert
from sqlalchemy.orm import Session

from energy_pipelines.core.database.table_models import AlgosOutput, FailingAlgosOutput, PriceData

logger = logging.getLogger(__name__)


def upsert_valid_energy_prices(session: Session, prices: DataFrame, update_on_conflict: bool) -> None:
    stmt = insert(PriceData).values(prices.to_dict(orient="records"))

    try:
        price_exists = _check_price_existence(
            session=session,
            timestamps=prices[PriceData.timestamp.key],
            price_metadata_ids=prices[PriceData.price_metadata_id.key],
        )
    except OperationalError as e:
        raise OperationalError(f"An error occurred while checking price existence: {e}") from e

    if price_exists:
        logger.info("Some/all energy prices already exist in the database.")

    stmt = _handle_upsertion_policy(
        stmt=stmt,
        table2insert=prices,
        table_exists=price_exists,
        primary_keys=[PriceData.timestamp.key, PriceData.price_metadata_id.key],
        cols2exclude_as_mapper={
            column.name: getattr(stmt.excluded, column.name)
            for column in PriceData.__table__.columns
            if not column.primary_key
        },
        update_on_conflict=update_on_conflict,
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        raise Exception("An error occurred while trying to upsert temperature schedule values.") from e


def upsert_valid_temp_schedule(
    session: Session,
    temp_schedule: DataFrame,
    update_on_conflict: bool,
) -> None:
    stmt = insert(AlgosOutput).values(temp_schedule.to_dict(orient="records"))

    try:
        schedule_exists = _check_temp_schedule_existence(
            session=session,
            timestamps=temp_schedule[AlgosOutput.timestamp.key],
            site_ids=temp_schedule[AlgosOutput.site_id.key],
            algo_ids=temp_schedule[AlgosOutput.algo_id.key],
        )
    except OperationalError as e:
        raise OperationalError(f"An error occurred while checking temperature schedule existence: {e}") from e

    if schedule_exists:
        logger.info("Some/all temperature schedule values already exist in the database.")

    stmt = _handle_upsertion_policy(
        stmt=stmt,
        table2insert=temp_schedule,
        table_exists=schedule_exists,
        primary_keys=[AlgosOutput.timestamp.key, AlgosOutput.site_id.key, AlgosOutput.algo_id.key],
        cols2exclude_as_mapper={
            column.name: getattr(stmt.excluded, column.name)
            for column in AlgosOutput.__table__.columns
            if not column.primary_key
        },
        update_on_conflict=update_on_conflict,
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        session.rollback()
        raise Exception("An error occurred while trying to upsert temperature schedule values.") from e


def upsert_failing_temp_schedule(
    session: Session,
    preprocessed_failing_algos_output: DataFrame,
) -> None:
    stmt = insert(FailingAlgosOutput).values(preprocessed_failing_algos_output.to_dict(orient="records"))

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        session.rollback()
        raise Exception("An error occurred while trying to upsert temperature schedule values.") from e


def _check_price_existence(
    session: Session, timestamps: Series[datetime], price_metadata_ids: Series[int]
) -> bool:
    keys = list(zip(timestamps.tolist(), price_metadata_ids.tolist(), strict=True))

    if not keys:
        return False

    stmt = select(exists().where(tuple_(PriceData.timestamp, PriceData.price_metadata_id).in_(keys)))

    return bool(session.scalar(stmt))


def _check_temp_schedule_existence(
    session: Session, timestamps: Series[datetime], site_ids: Series[int], algo_ids: Series[int]
) -> bool:
    keys = list(zip(timestamps.tolist(), site_ids.tolist(), algo_ids.to_list(), strict=True))

    if not keys:
        return False

    stmt = select(
        exists().where(tuple_(AlgosOutput.timestamp, AlgosOutput.site_id, AlgosOutput.algo_id).in_(keys))
    )

    return bool(session.scalar(stmt))


def _handle_upsertion_policy(
    stmt: Insert,
    table2insert: DataFrame,
    table_exists: bool,
    primary_keys: list[str],
    cols2exclude_as_mapper: dict[str, Any],
    update_on_conflict: bool,
) -> Insert:
    if update_on_conflict:
        stmt = stmt.on_conflict_do_update(
            index_elements=primary_keys,
            set_=cols2exclude_as_mapper,
        )

        if table_exists:
            logger.info(
                f"{len(table2insert)} temperature schedule values will be updated in the database"
                f" successfully."
            )
        else:
            logger.info(
                f"{len(table2insert)} temperature schedule values will be upserted into the database"
                f" successfully."
            )
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=primary_keys)

        if table_exists:
            logger.info(
                "No data will be upserted to the DB since they are already exist."
                " If you want to update them, set the parameter 'update_on_conflict' to True."
            )
        else:
            logger.info(
                f"{len(table2insert)} temperature schedule values will be upserted into the database"
                f" successfully."
            )

    return stmt
