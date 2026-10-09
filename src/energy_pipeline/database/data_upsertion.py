import logging
from datetime import datetime

from pandas import DataFrame, Series
from sqlalchemy import exists, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.energy_pipeline.database.models import PriceData
from utils.custom_objects import DbId

logger = logging.getLogger(__name__)


def upsert_energy_prices_to_db(session: Session, prices: DataFrame, update_on_conflict: bool) -> None:
    stmt = insert(PriceData).values(prices.to_dict(orient="records"))

    price_exists = _check_price_existence(
        session=session,
        timestamps=prices[PriceData.timestamp.key],
        price_metadata_ids=prices[PriceData.price_metadata_id.key],
    )

    if price_exists:
        logger.info("Some/all energy prices already exist in the database.")

    if update_on_conflict:
        stmt = stmt.on_conflict_do_update(
            index_elements=[PriceData.timestamp, PriceData.price_metadata_id],
            set_={"energy_price": stmt.excluded.energy_price},
        )

        if price_exists:
            logger.info(f"{len(prices)} energy prices have been updated in the database successfully.")
        else:
            logger.info(f"{len(prices)} energy prices have been upserted into the database successfully.")
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=[PriceData.timestamp, PriceData.price_metadata_id])

        if price_exists:
            logger.info(
                "No data has been upserted to the DB since they are already exist. If you want to update them,"
                " set the parameter 'update_on_conflict' to True."
            )
        else:
            logger.info(f"{len(prices)} energy prices have been upserted into the database successfully.")

    session.execute(stmt)
    session.commit()


def _check_price_existence(session: Session, timestamps: Series[datetime], price_metadata_ids: Series[DbId]) -> bool:
    keys = list(zip(timestamps.tolist(), price_metadata_ids.tolist(), strict=True))

    if not keys:
        return False

    stmt = select(exists().where(tuple_(PriceData.timestamp, PriceData.price_metadata_id).in_(keys)))

    return bool(session.scalar(stmt))
